# DynamicUrbanMobilityFabric

Structural coordination for evolving urban mobility graphs on GenLayer.

This primitive stores mobility nodes and typed connections, then applies bounded graph changes through a consensus-checked state transition. It is deliberately not a traffic oracle: it does not claim that a vehicle moved, that a route is fastest, or that a physical service was delivered.

## Why GenLayer

The transition report is independently recomputed by the leader and validators. Exact equality covers the operation, parent head, node references, edge constraints, resulting graph, and deterministic result root. A mismatch prevents the state transition.

## State machine

```text
CREATED --add_node--> ACTIVE
ACTIVE --propose_change--> PROPOSED
PROPOSED --apply_change + agreement--> APPLIED
PROPOSED --invalid--> REJECTED
PROPOSED --expired--> EXPIRED
PROPOSED --stale parent--> STALE
```

Applied versions and event records are append-only. Every proposal binds its network ID, parent version, parent root, proposer, and exact change fields. Cross-network and replayed proposals are rejected.

## Contract API

- `create_network(network_id, name)`
- `add_node(network_id, node_id, node_type, capacity)`
- `propose_change(network_id, proposal_id, parent_version, operation, connection_id, source, target, connection_type, deadline)`
- `apply_change(network_id, proposal_id)`
- `get_network`, `get_proposal`, `get_result`, `get_event`

Only `ADD_CONNECTION` and `REMOVE_CONNECTION` are included in this bounded primitive. Nodes must exist, connection pairs cannot duplicate, self-loops are rejected, and parent heads must match.

## Development

```powershell
npm install -g genlayer
genlayer network set studionet
genvm-lint check contracts/DynamicUrbanMobilityFabric.py --json
genlayer deploy --contract contracts/DynamicUrbanMobilityFabric.py
```

StudioNet is gasless. Inspect every receipt for both `FINALIZED` and successful execution; a finalized failed transaction is not proof.

## Scope and security

The contract verifies graph structure only. It never treats caller text, confidence, a hash length, or a provider summary as proof of physical mobility. Capacity and node metadata are planning fields, not measurements. Applications must bind real-world telemetry through a separate oracle with its own evidence policy.

## License

MIT
