"""
Cryptographic evidence verification tests for SovereignStack MCP integration.
"""

from integrations.mcp.contracts import CoreEngineOASAAdapter
from integrations.mcp.server import (
    evaluate_action,
    execute_action,
    set_current_principal,
    set_oasa_service,
    verify_evidence,
)


def test_mcp_evidence_verification_positive():
    """Verify legitimate Action Envelope passes mathematical verification."""
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    set_current_principal("agent://devops-bot")

    # Authorize & Execute
    eval_res = evaluate_action(
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
        parameters={"grace_period": 30},
    )
    exec_res = execute_action(
        action_id=eval_res["action_id"],
        token_id=eval_res["token_id"],
        target_uri="morpheus://vm/staging-web-01",
        payload={"grace_period": 30},
    )

    envelope = exec_res["envelope"]
    provider_audit = exec_res["provider_audit"]

    # Verify through MCP tool
    verif = verify_evidence(
        envelope=envelope,
        request_payload={"grace_period": 30},
        provider_audit_payload=provider_audit,
    )
    assert verif["verified"] is True
    assert verif["status"] == "PASS"
    assert verif["checks"]["signature"] == "PASS"
    assert verif["checks"]["hashes"] == "PASS"


def test_mcp_evidence_verification_tampering_rejected():
    """Tampering with Action Envelope payload or signature fails verification."""
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    set_current_principal("agent://devops-bot")

    eval_res = evaluate_action(
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
        parameters={"grace_period": 30},
    )
    exec_res = execute_action(
        action_id=eval_res["action_id"],
        token_id=eval_res["token_id"],
        target_uri="morpheus://vm/staging-web-01",
        payload={"grace_period": 30},
    )

    tampered_envelope = dict(exec_res["envelope"])
    # Tamper with target URI in envelope
    tampered_envelope["target"] = {"uri": "morpheus://vm/production-db-01"}

    verif = verify_evidence(
        envelope=tampered_envelope,
        request_payload={"grace_period": 30},
        provider_audit_payload=exec_res["provider_audit"],
    )
    assert verif["verified"] is False
    assert verif["status"] == "FAIL"
