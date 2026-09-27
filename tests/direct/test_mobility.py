import time


def test_graph_rules_and_replay_guard(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/DynamicUrbanMobilityFabric.py")
    direct_vm.sender = direct_alice
    contract.create_network("city-demo", "Demo City")
    contract.add_node("city-demo", "zone-a", "ZONE", 1000)
    contract.add_node("city-demo", "hub-a", "HUB", 5000)
    network = contract.get_network("city-demo")
    assert network["status"] == "ACTIVE"
    assert network["version"] == 0

    deadline = int(time.time()) + 3600
    with direct_vm.expect_revert("proposed connection violates graph rules"):
        contract.propose_change("city-demo", "bad", 0, "ADD_CONNECTION", "bad", "zone-a", "missing", "BUS", deadline)

    contract.propose_change("city-demo", "edge-1", 0, "ADD_CONNECTION", "edge-1", "zone-a", "hub-a", "BUS", deadline)
    with direct_vm.expect_revert("active network and unique proposal required"):
        contract.propose_change("city-demo", "edge-1", 0, "ADD_CONNECTION", "edge-1", "zone-a", "hub-a", "BUS", deadline)
