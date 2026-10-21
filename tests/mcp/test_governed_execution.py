"""
Governed execution, anti-theater, and client proxy tests for SovereignStack MCP integration.
"""

from integrations.mcp.contracts import CoreEngineOASAAdapter
from integrations.mcp.server import (
    evaluate_action,
    execute_action,
    get_action,
    get_provenance,
    set_current_principal,
    set_oasa_service,
)
from integrations.mcp.client import GovernedMCPClient


def test_golden_path_execution():
    """Verify end-to-end golden path: evaluate -> execute -> record."""
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    set_current_principal("agent://devops-bot")

    # 1. EVALUATE (Authorize)
    eval_res = evaluate_action(
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
        parameters={"grace_period": 30},
    )
    assert eval_res["decision"] == "ALLOW"
    assert eval_res["allowed"] is True
    assert eval_res["token_id"] is not None
    action_id = eval_res["action_id"]
    token_id = eval_res["token_id"]

    # 2. EXECUTE
    exec_res = execute_action(
        action_id=action_id,
        token_id=token_id,
        target_uri="morpheus://vm/staging-web-01",
        payload={"grace_period": 30},
    )
    assert exec_res["status"] == "SUCCESS"
    assert exec_res["provider_action_id"] is not None

    # 3. RECORD
    act_rec = get_action(action_id)
    assert act_rec["status"] == "SUCCESS"
    assert act_rec["action"]["action_id"] == action_id

    prov_rec = get_provenance(action_id)
    assert prov_rec["status"] == "SUCCESS"
    assert prov_rec["provenance"]["execution"]["status"] == "SUCCESS"


def test_anti_theater_destructive_action_blocked():
    """
    Anti-theater invariant: Destructive action is denied and never executes against provider.
    """
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    set_current_principal("agent://customer-support-bot")

    morpheus_adapter = adapter.engine.get_adapter_for_target("morpheus://vm/production-db-01")
    calls_before = morpheus_adapter.provider_call_count

    eval_res = evaluate_action(
        capability_id="infrastructure.vm.delete",
        target_uri="morpheus://vm/production-db-01",
    )
    assert eval_res["decision"] == "DENY"
    assert eval_res["allowed"] is False
    assert "destructive actions strictly prohibited" in eval_res["reason"]

    # Zero calls made to provider
    assert morpheus_adapter.provider_call_count == calls_before


def test_token_replay_rejected():
    """Single-use authorization tokens cannot be replayed."""
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    set_current_principal("agent://devops-bot")

    eval_res = evaluate_action(
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
    )
    action_id = eval_res["action_id"]
    token_id = eval_res["token_id"]

    # First execution succeeds
    first_res = execute_action(
        action_id=action_id,
        token_id=token_id,
        target_uri="morpheus://vm/staging-web-01",
    )
    assert first_res["status"] == "SUCCESS"

    # Replay execution must fail
    replay_res = execute_action(
        action_id=action_id,
        token_id=token_id,
        target_uri="morpheus://vm/staging-web-01",
    )
    assert replay_res["status"] == "FAIL"
    assert "CONSUMED" in replay_res["error"]


def test_governed_mcp_client_proxy():
    """Verify GovernedMCPClient evaluates policies and enforces kill switch on third-party tools."""
    adapter = CoreEngineOASAAdapter()
    client = GovernedMCPClient(oasa_service=adapter, principal="agent://devops-bot")

    # Register a third party tool
    def mock_vm_restart(vm_id: str):
        return {"restarted": vm_id}

    def mock_vm_delete(vm_id: str):
        return {"deleted": vm_id}

    client.register_tool(
        "restart_vm",
        mock_vm_restart,
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
    )
    client.register_tool(
        "delete_vm",
        mock_vm_delete,
        capability_id="infrastructure.vm.delete",
        target_uri="morpheus://vm/staging-web-01",
    )

    # Calling restart tool passes governance
    res_allow = client.call_tool("restart_vm", arguments={"vm_id": "staging-01"})
    assert res_allow["status"] == "SUCCESS"
    assert res_allow["decision"] == "ALLOW"
    assert client.call_count["restart_vm"] == 1

    # Calling delete tool is blocked by policy (anti-theater)
    res_deny = client.call_tool("delete_vm", arguments={"vm_id": "staging-01"})
    assert res_deny["status"] == "DENIED"
    assert res_deny["decision"] == "DENY"
    assert client.call_count["delete_vm"] == 0  # Zero calls!

    # Trigger emergency kill switch
    client.trigger_kill_switch()
    res_killed = client.call_tool("restart_vm", arguments={"vm_id": "staging-01"})
    assert res_killed["status"] == "DENIED"
    assert "KILL_SWITCH_ACTIVE" in res_killed["reason"]
    assert client.call_count["restart_vm"] == 1  # Still 1, call did not proceed
