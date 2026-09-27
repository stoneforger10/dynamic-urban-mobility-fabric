# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from genlayer import *

NODE_TYPES = ("STATION", "ZONE", "HUB", "ROAD_SEGMENT", "TRANSIT_POINT", "SERVICE_AREA")
EDGE_TYPES = ("ROAD", "RAIL", "BUS", "WALKWAY", "TRANSFER")
OPERATIONS = ("ADD_CONNECTION", "REMOVE_CONNECTION")

def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def key(network_id: str, item_id: str) -> str:
    return network_id + ":" + item_id

def valid_id(value: str) -> bool:
    return 1 <= len(value) <= 48 and all(c in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in value)

def now() -> int:
    return int(datetime.fromisoformat(gl.message_raw["datetime"]).timestamp())

@allow_storage
@dataclass
class Network:
    owner: Address
    name: str
    status: str
    version: u256
    nodes: str
    connections: str
    root: str

@allow_storage
@dataclass
class Proposal:
    network_id: str
    proposer: Address
    parent_version: u256
    parent_root: str
    operation: str
    connection_id: str
    source: str
    target: str
    connection_type: str
    deadline: u256
    state: str
    result_root: str

class DynamicUrbanMobilityFabric(gl.Contract):
    networks: TreeMap[str, Network]
    proposals: TreeMap[str, Proposal]
    events: TreeMap[str, str]
    results: TreeMap[str, str]

    def __init__(self) -> None:
        pass

    def _owned(self, network_id: str) -> Network:
        if network_id not in self.networks:
            raise gl.vm.UserError("[EXPECTED] unknown network")
        network = self.networks[network_id]
        if network.owner != gl.message.sender_address:
            raise gl.vm.UserError("[EXPECTED] network owner required")
        return network

    def _simulate(self, network: Network, proposal: Proposal) -> dict:
        nodes = json.loads(network.nodes)
        connections = json.loads(network.connections)
        if proposal.operation not in OPERATIONS:
            return {"valid": False, "reason": "operation", "connections": connections}
        if proposal.connection_id == "" or not valid_id(proposal.connection_id):
            return {"valid": False, "reason": "connection_id", "connections": connections}
        if proposal.operation == "ADD_CONNECTION":
            if proposal.connection_id in connections:
                return {"valid": False, "reason": "duplicate_connection", "connections": connections}
            if proposal.source not in nodes or proposal.target not in nodes:
                return {"valid": False, "reason": "unknown_node", "connections": connections}
            if proposal.source == proposal.target or proposal.connection_type not in EDGE_TYPES:
                return {"valid": False, "reason": "invalid_edge", "connections": connections}
            for value in connections.values():
                if value["source"] == proposal.source and value["target"] == proposal.target:
                    return {"valid": False, "reason": "duplicate_pair", "connections": connections}
            connections[proposal.connection_id] = {"source": proposal.source, "target": proposal.target, "type": proposal.connection_type}
        elif proposal.connection_id not in connections:
            return {"valid": False, "reason": "missing_connection", "connections": connections}
        else:
            del connections[proposal.connection_id]
        return {"valid": True, "reason": "", "connections": connections}

    def _report(self, network_id: str, proposal_id: str, network: Network, proposal: Proposal) -> dict:
        simulated = self._simulate(network, proposal)
        packet = {"protocol": "dynamic-urban-mobility-v1", "network": network_id, "proposal": proposal_id,
                  "parent_version": int(proposal.parent_version), "parent_root": proposal.parent_root,
                  "operation": proposal.operation, "connection_id": proposal.connection_id,
                  "source": proposal.source, "target": proposal.target,
                  "connection_type": proposal.connection_type, "valid": simulated["valid"],
                  "reason": simulated["reason"], "result_graph": simulated["connections"]}
        packet["result_root"] = digest(canonical(packet))
        return packet

    def _finish(self, network_id: str, proposal_id: str, network: Network, proposal: Proposal,
                state: str, report: dict) -> None:
        packet = {"state": state, "report": report, "network": network_id, "proposal": proposal_id}
        proposal.state = state
        proposal.result_root = digest(canonical(packet))
        self.results[key(network_id, proposal_id)] = canonical(packet)
        if state == "APPLIED":
            network.connections = canonical(report["result_graph"])
            network.version += 1
            network.root = digest(canonical({"network": network_id, "version": int(network.version),
                "nodes": json.loads(network.nodes), "connections": json.loads(network.connections),
                "parent_root": proposal.parent_root, "proposal_root": proposal.result_root}))
            self.events[key(network_id, str(int(network.version)))] = canonical({
                "version": int(network.version), "root": network.root, "proposal": proposal_id,
                "proposal_root": proposal.result_root})
            self.networks[network_id] = network
        self.proposals[key(network_id, proposal_id)] = proposal

    @gl.public.write
    def create_network(self, network_id: str, name: str) -> None:
        if not valid_id(network_id) or network_id in self.networks:
            raise gl.vm.UserError("[EXPECTED] unique network ID required")
        if not 1 <= len(name) <= 120:
            raise gl.vm.UserError("[EXPECTED] bounded network name required")
        self.networks[network_id] = Network(gl.message.sender_address, name, "CREATED", 0, "{}", "{}",
            digest(canonical({"network": network_id, "version": 0, "nodes": {}, "connections": {}})))

    @gl.public.write
    def add_node(self, network_id: str, node_id: str, node_type: str, capacity: int) -> None:
        network = self._owned(network_id)
        if network.status not in ("CREATED", "ACTIVE"):
            raise gl.vm.UserError("[EXPECTED] editable network required")
        nodes = json.loads(network.nodes)
        if len(nodes) >= 128 or not valid_id(node_id) or node_id in nodes:
            raise gl.vm.UserError("[EXPECTED] unique bounded node required")
        if node_type not in NODE_TYPES or not 0 <= capacity <= 1000000000:
            raise gl.vm.UserError("[EXPECTED] valid node type and capacity required")
        nodes[node_id] = {"type": node_type, "capacity": capacity}
        network.nodes = canonical(nodes)
        network.status = "ACTIVE"
        network.root = digest(canonical({"network": network_id, "version": int(network.version),
            "nodes": nodes, "connections": json.loads(network.connections)}))
        self.networks[network_id] = network

    @gl.public.write
    def propose_change(self, network_id: str, proposal_id: str, parent_version: int, operation: str,
                       connection_id: str, source: str, target: str, connection_type: str, deadline: int) -> None:
        network = self._owned(network_id)
        proposal_key = key(network_id, proposal_id)
        if network.status != "ACTIVE" or not valid_id(proposal_id) or proposal_key in self.proposals:
            raise gl.vm.UserError("[EXPECTED] active network and unique proposal required")
        if parent_version != int(network.version) or not now() < deadline <= now() + 86400:
            raise gl.vm.UserError("[EXPECTED] current version and deadline within one day required")
        if operation not in OPERATIONS or not valid_id(connection_id):
            raise gl.vm.UserError("[EXPECTED] valid operation and connection required")
        proposal = Proposal(network_id, gl.message.sender_address, parent_version, network.root, operation,
            connection_id, source, target, connection_type, deadline, "PROPOSED", "")
        if operation == "ADD_CONNECTION" and not self._simulate(network, proposal)["valid"]:
            raise gl.vm.UserError("[EXPECTED] proposed connection violates graph rules")
        if operation == "REMOVE_CONNECTION" and connection_id not in json.loads(network.connections):
            raise gl.vm.UserError("[EXPECTED] connection does not exist")
        self.proposals[proposal_key] = proposal

    @gl.public.write
    def apply_change(self, network_id: str, proposal_id: str) -> None:
        network = self._owned(network_id)
        proposal_key = key(network_id, proposal_id)
        if proposal_key not in self.proposals:
            raise gl.vm.UserError("[EXPECTED] proposal not found")
        proposal = self.proposals[proposal_key]
        if proposal.network_id != network_id or proposal.state != "PROPOSED":
            raise gl.vm.UserError("[EXPECTED] proposal is terminal or cross-network")
        if now() >= int(proposal.deadline):
            self._finish(network_id, proposal_id, network, proposal, "EXPIRED", {"reason": "deadline"})
            return
        if int(proposal.parent_version) != int(network.version) or proposal.parent_root != network.root:
            self._finish(network_id, proposal_id, network, proposal, "STALE", {"reason": "parent_head"})
            return
        def observe() -> dict:
            return self._report(network_id, proposal_id, network, proposal)
        def validate(leader: gl.vm.Result) -> bool:
            return isinstance(leader, gl.vm.Return) and leader.calldata == self._report(network_id, proposal_id, network, proposal)
        report = gl.vm.run_nondet_unsafe(observe, validate)
        self._finish(network_id, proposal_id, network, proposal, "APPLIED" if report["valid"] else "REJECTED", report)

    @gl.public.view
    def get_network(self, network_id: str) -> dict:
        network = self.networks[network_id]
        return {"owner": network.owner, "name": network.name, "status": network.status,
                "version": network.version, "root": network.root,
                "nodes": json.loads(network.nodes), "connections": json.loads(network.connections)}

    @gl.public.view
    def get_proposal(self, network_id: str, proposal_id: str) -> dict:
        proposal = self.proposals[key(network_id, proposal_id)]
        return {"network": proposal.network_id, "proposer": proposal.proposer,
                "parent_version": proposal.parent_version, "parent_root": proposal.parent_root,
                "operation": proposal.operation, "connection_id": proposal.connection_id,
                "source": proposal.source, "target": proposal.target,
                "connection_type": proposal.connection_type, "deadline": proposal.deadline,
                "state": proposal.state, "result_root": proposal.result_root}

    @gl.public.view
    def get_result(self, network_id: str, proposal_id: str) -> str:
        return self.results[key(network_id, proposal_id)]

    @gl.public.view
    def get_event(self, network_id: str, version: int) -> str:
        return self.events[key(network_id, str(version))]
