"""
SovereignStack v0.6 Normative Conformance Test Suite (16 Tests)
Specification: OASA v0.6 Governed Autonomous Action
"""

import time
import pytest
from conformance.core_engine import CoreEngine
from conformance.action_envelope import (
    build_evidence_package,
    verify_evidence_package,
    canonical_json_bytes,
    sha256_hex,
)
from integrations.morpheus.adapter.morpheus_adapter import MorpheusAdapter


@pytest.fixture
def setup_engine():
    engine = CoreEngine()
    morpheus_adapter = MorpheusAdapter()
    engine.register_adapter("morpheus", morpheus_adapter)
    return engine, morpheus_adapter


# ---------------------------------------------------------------------------
# AUTH-001: Authorization Precedes Execution
# ---------------------------------------------------------------------------
def test_authorization_precedes_execution(setup_engine):
    engine, adapter = setup_engine
    # Attempting to execute an action that was never authorized
    result = engine.execute(
        action_id="act_unauthorized_999",
        token_id="tok_fake_123",
        presenting_actor_id="agent://support-bot",
        target_uri="morpheus://vm/staging-web-01",
    )
    assert result["status"] == "FAIL"
    assert result["error"] == "ACTION_NOT_FOUND"
    assert adapter.provider_call_count == 0


# ---------------------------------------------------------------------------
# AUTH-002: Anti-Theater Test A — Denied Action Never Reaches Infrastructure
# ---------------------------------------------------------------------------
def test_unauthorized_action_never_reaches_provider(setup_engine):
    """
    ANTI-THEATER GATE:
    Agent requests destructive delete on production.
    Decision must be DENY.
    Provider actions must be strictly 0.
    Denial evidence must be cryptographically recorded.
    """
    engine, adapter = setup_engine

    initial_provider_calls = adapter.provider_call_count

    auth_response = engine.authorize(
        actor_id="agent://customer-support-bot",
        actor_type="agent",
        capability_id="infrastructure.vm.delete",
        target_uri="morpheus://vm/production-db-01",
        delegation=[
            {"delegator": "human://operator", "delegate": "agent://supervisor"},
            {"delegator": "agent://supervisor", "delegate": "agent://customer-support-bot"},
        ],
    )

    # 1. Assert Decision is DENY
    assert auth_response["decision"] == "deny"
    assert "token_id" not in auth_response
    action_id = auth_response["action_id"]

    # 2. Attempting to execute a denied action fails immediately
    exec_response = engine.execute(
        action_id=action_id,
        token_id="tok_non_existent",
        presenting_actor_id="agent://customer-support-bot",
        target_uri="morpheus://vm/production-db-01",
    )
    assert exec_response["status"] == "FAIL"
    assert exec_response["error"] == "CANNOT_EXECUTE_DENIED_ACTION"

    # 3. CRITICAL ANTI-THEATER ASSERTION: Provider execution count MUST be exactly 0
    assert adapter.provider_call_count == initial_provider_calls == 0

    # 4. Assert Denial Evidence is valid and cryptographically signed
    denial_envelope = auth_response["envelope"]
    assert denial_envelope["authorization"]["decision"] == "deny"
    valid, checks = CoreEngine.verify(denial_envelope)
    assert valid is True
    assert checks["signature"] == "PASS"


# ---------------------------------------------------------------------------
# AUTH-003: Authorization Token Expires
# ---------------------------------------------------------------------------
def test_authorization_token_expires(setup_engine):
    engine, adapter = setup_engine
    auth_response = engine.authorize(
        actor_id="agent://ops-bot",
        actor_type="agent",
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
        ttl_seconds=1,  # Short 1-second TTL
    )
    assert auth_response["decision"] == "allow"
    action_id = auth_response["action_id"]
    token_id = auth_response["token_id"]

    # Wait for expiry
    time.sleep(1.1)

    exec_result = engine.execute(
        action_id=action_id,
        token_id=token_id,
        presenting_actor_id="agent://ops-bot",
        target_uri="morpheus://vm/staging-web-01",
    )
    assert exec_result["status"] == "FAIL"
    assert exec_result["error"] == "TOKEN_EXPIRED"
    assert adapter.provider_call_count == 0


# ---------------------------------------------------------------------------
# AUTH-004: Authorization Token Cannot Be Replayed (Atomic Single-Use)
# ---------------------------------------------------------------------------
def test_authorization_token_cannot_be_replayed(setup_engine):
    engine, adapter = setup_engine
    auth_response = engine.authorize(
        actor_id="agent://ops-bot",
        actor_type="agent",
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
    )
    action_id = auth_response["action_id"]
    token_id = auth_response["token_id"]

    # First execution succeeds
    exec1 = engine.execute(
        action_id=action_id,
        token_id=token_id,
        presenting_actor_id="agent://ops-bot",
        target_uri="morpheus://vm/staging-web-01",
    )
    assert exec1["status"] == "SUCCESS"
    assert adapter.provider_call_count == 1

    # Replay attempt fails immediately
    exec2 = engine.execute(
        action_id=action_id,
        token_id=token_id,
        presenting_actor_id="agent://ops-bot",
        target_uri="morpheus://vm/staging-web-01",
    )
    assert exec2["status"] == "FAIL"
    assert exec2["error"] == "TOKEN_ALREADY_CONSUMED"
    # Provider was NOT executed a second time
    assert adapter.provider_call_count == 1


# ---------------------------------------------------------------------------
# AUTH-005: Capability Cannot Be Escalated
# ---------------------------------------------------------------------------
def test_capability_cannot_be_escalated(setup_engine):
    engine, adapter = setup_engine
    auth_response = engine.authorize(
        actor_id="agent://junior-bot",
        actor_type="agent",
        capability_id="infrastructure.network.reconfigure_firewall",  # Escalated capability
        target_uri="morpheus://vm/staging-web-01",
    )
    assert auth_response["decision"] == "deny"
    assert "capability 'infrastructure.network.reconfigure_firewall' not granted" in auth_response["reason"]
    assert adapter.provider_call_count == 0


# ---------------------------------------------------------------------------
# AUTH-006: Target Cannot Be Changed After Authorization
# ---------------------------------------------------------------------------
def test_target_cannot_be_changed_after_authorization(setup_engine):
    engine, adapter = setup_engine
    auth_response = engine.authorize(
        actor_id="agent://ops-bot",
        actor_type="agent",
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
    )
    action_id = auth_response["action_id"]
    token_id = auth_response["token_id"]

    # Attempting to execute with a different target URI than authorized
    exec_result = engine.execute(
        action_id=action_id,
        token_id=token_id,
        presenting_actor_id="agent://ops-bot",
        target_uri="morpheus://vm/production-web-99",  # Tampered target
    )
    assert exec_result["status"] == "FAIL"
    assert exec_result["error"] == "TARGET_MISMATCH"
    assert adapter.provider_call_count == 0


# ---------------------------------------------------------------------------
# ENV-001: Action Envelope Has Unique ID
# ---------------------------------------------------------------------------
def test_action_envelope_has_unique_id(setup_engine):
    engine, _ = setup_engine
    auth1 = engine.authorize("agent://bot", "agent", "infrastructure.vm.status", "morpheus://vm/staging-web-01")
    auth2 = engine.authorize("agent://bot", "agent", "infrastructure.vm.status", "morpheus://vm/staging-web-01")
    assert auth1["action_id"] != auth2["action_id"]
    assert auth1["action_id"].startswith("act_")
    assert auth2["action_id"].startswith("act_")


# ---------------------------------------------------------------------------
# ENV-002: Actor Is Attributable
# ---------------------------------------------------------------------------
def test_actor_is_attributable(setup_engine):
    engine, adapter = setup_engine
    auth = engine.authorize("agent://authorized-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    action_id = auth["action_id"]
    token_id = auth["token_id"]

    # Different actor presents the token
    exec_result = engine.execute(
        action_id=action_id,
        token_id=token_id,
        presenting_actor_id="agent://impostor-bot",  # Impostor actor
        target_uri="morpheus://vm/staging-web-01",
    )
    assert exec_result["status"] == "FAIL"
    assert exec_result["error"] == "ACTOR_MISMATCH"
    assert adapter.provider_call_count == 0


# ---------------------------------------------------------------------------
# ENV-003: Capability Is Explicit
# ---------------------------------------------------------------------------
def test_capability_is_explicit(setup_engine):
    engine, _ = setup_engine
    auth = engine.authorize("agent://bot", "agent", "infrastructure.vm.status", "morpheus://vm/staging-web-01")
    envelope = auth["envelope"]
    assert "capability" in envelope
    assert envelope["capability"]["id"] == "infrastructure.vm.status"


# ---------------------------------------------------------------------------
# ENV-004: Target Is Explicit
# ---------------------------------------------------------------------------
def test_target_is_explicit(setup_engine):
    engine, _ = setup_engine
    target = "morpheus://vm/staging-web-01"
    auth = engine.authorize("agent://bot", "agent", "infrastructure.vm.status", target)
    envelope = auth["envelope"]
    assert "target" in envelope
    assert envelope["target"]["uri"] == target


# ---------------------------------------------------------------------------
# DEL-001: Delegation Chain Is Preserved
# ---------------------------------------------------------------------------
def test_delegation_chain_is_preserved(setup_engine):
    engine, _ = setup_engine
    chain = [
        {"delegator": "human://lead-architect", "delegate": "agent://supervisor"},
        {"delegator": "agent://supervisor", "delegate": "agent://worker"},
    ]
    auth = engine.authorize(
        actor_id="agent://worker",
        actor_type="agent",
        capability_id="infrastructure.vm.status",
        target_uri="morpheus://vm/staging-web-01",
        delegation=chain,
    )
    envelope = auth["envelope"]
    assert envelope["delegation"] == chain


# ---------------------------------------------------------------------------
# DEL-002: Invalid Delegation Is Rejected
# ---------------------------------------------------------------------------
def test_invalid_delegation_is_rejected(setup_engine):
    engine, _ = setup_engine
    malformed_chain = [
        {"delegator": "human://lead-architect", "delegate": "agent://supervisor"},
        {"delegator": "unverified-anonymous-entity", "delegate": "agent://worker"},
    ]
    auth = engine.authorize(
        actor_id="agent://worker",
        actor_type="agent",
        capability_id="infrastructure.vm.status",
        target_uri="morpheus://vm/staging-web-01",
        delegation=malformed_chain,
    )
    assert auth["decision"] == "deny"
    assert "Invalid delegation link" in auth["reason"]


# ---------------------------------------------------------------------------
# PROV-001: Provider Action ID Is Linked
# ---------------------------------------------------------------------------
def test_provider_action_id_is_linked(setup_engine):
    engine, adapter = setup_engine
    auth = engine.authorize("agent://ops-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    action_id = auth["action_id"]
    token_id = auth["token_id"]

    exec_result = engine.execute(action_id, token_id, "agent://ops-bot", "morpheus://vm/staging-web-01")
    assert exec_result["status"] == "SUCCESS"
    provider_id = exec_result["provider_action_id"]
    assert provider_id.startswith("morph-task-")

    envelope = exec_result["envelope"]
    assert envelope["execution"]["provider"] == "morpheus"
    assert envelope["execution"]["provider_action_id"] == provider_id


# ---------------------------------------------------------------------------
# EVID-001: Test B — Authorized Action Produces Verifiable Evidence
# ---------------------------------------------------------------------------
def test_authorized_action_produces_verifiable_evidence(setup_engine):
    """
    KILLER TEST B (Golden Path Verifiable Evidence):
    ALLOW -> execution -> provider action ID -> native provider evidence -> independent verify.
    """
    engine, adapter = setup_engine
    auth = engine.authorize("agent://ops-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    assert auth["decision"] == "allow"
    action_id = auth["action_id"]
    token_id = auth["token_id"]

    exec_result = engine.execute(action_id, token_id, "agent://ops-bot", "morpheus://vm/staging-web-01")
    assert exec_result["status"] == "SUCCESS"

    envelope = exec_result["envelope"]
    # Independent verification
    valid, checks = CoreEngine.verify(envelope)
    assert valid is True
    assert checks["structure"] == "PASS"
    assert checks["signature"] == "PASS"
    assert checks["hashes"] == "PASS"
    assert checks["provider_linkage"] == "PASS"


# ---------------------------------------------------------------------------
# EVID-002: Tampered Evidence Fails Verification
# ---------------------------------------------------------------------------
def test_tampered_evidence_fails_verification(setup_engine):
    engine, _ = setup_engine
    auth = engine.authorize("agent://ops-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    action_id = auth["action_id"]
    token_id = auth["token_id"]

    exec_result = engine.execute(action_id, token_id, "agent://ops-bot", "morpheus://vm/staging-web-01")
    envelope = exec_result["envelope"]

    # Tampering with target URI post-signing
    tampered_envelope = dict(envelope)
    tampered_envelope["target"] = {"uri": "morpheus://vm/production-db-hacked"}

    valid, checks = CoreEngine.verify(tampered_envelope)
    assert valid is False
    assert checks["signature"] == "FAIL: Signature mismatch"

# ---------------------------------------------------------------------------
# EVID-003: Authorized Action Must Have Provider Evidence
# ---------------------------------------------------------------------------
def test_authorized_action_must_have_provider_evidence(setup_engine):
    engine, _ = setup_engine
    auth = engine.authorize("agent://ops-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    action_id = auth["action_id"]
    token_id = auth["token_id"]

    exec_result = engine.execute(action_id, token_id, "agent://ops-bot", "morpheus://vm/staging-web-01")
    envelope = exec_result["envelope"]

    import copy

    # Tampering A: remove provider_action_id but keep status SUCCESS
    tampered_env_a = copy.deepcopy(envelope)
    tampered_env_a["execution"].pop("provider_action_id", None)
    
    ev_a = tampered_env_a.pop("evidence")
    ev_a["hashes"]["execution"] = sha256_hex(canonical_json_bytes({
        "provider": tampered_env_a["execution"].get("provider"),
        "provider_action_id": tampered_env_a["execution"].get("provider_action_id")
    }))

    payload_to_sign_a = {k: v for k, v in tampered_env_a.items()}
    payload_to_sign_a["evidence_hashes"] = ev_a["hashes"]
    sig_a = engine.signer.sign_payload(payload_to_sign_a)
    tampered_env_a["evidence"] = ev_a
    tampered_env_a["evidence"]["signature"] = sig_a
    
    valid_a, checks_a = CoreEngine.verify(tampered_env_a)
    assert valid_a is False
    assert checks_a.get("provider_linkage", "") == "FAIL: Missing provider_action_id for successful action"

    # Tampering B: remove provider_audit from hashes
    tampered_env_b = copy.deepcopy(envelope)
    ev_b = tampered_env_b.pop("evidence")
    ev_b["hashes"].pop("provider_audit", None)
    
    payload_to_sign_b = {k: v for k, v in tampered_env_b.items()}
    payload_to_sign_b["evidence_hashes"] = ev_b["hashes"]
    sig_b = engine.signer.sign_payload(payload_to_sign_b)
    tampered_env_b["evidence"] = ev_b
    tampered_env_b["evidence"]["signature"] = sig_b

    valid_b, checks_b = CoreEngine.verify(tampered_env_b)
    assert valid_b is False
    assert checks_b.get("provider_linkage", "") == "FAIL: Missing provider_audit evidence for successful action"

    # EVID-003 STRENGTHENING: provider evidence must exist AND be independently
    # resolvable and verifiable via the OASA Evidence Package.
    provider_audit = exec_result["provider_audit"]

    # Positive case: valid evidence package independently verifies PASS.
    package = build_evidence_package(
        envelope,
        request_payload={},
        provider_audit_payload=provider_audit,
    )
    valid_pkg, checks_pkg = verify_evidence_package(package)
    assert valid_pkg is True
    assert checks_pkg["hashes"] == "PASS"
    assert checks_pkg["provider_linkage"] == "PASS"

    # Tampering C (P1.5): provider-audit payload does not match its claimed hash.
    tampered_audit = dict(provider_audit)
    tampered_audit["audit_event"] = {"event_type": "TAMPERED_LOG_ENTRY"}
    package_bad_audit = build_evidence_package(
        envelope,
        request_payload={},
        provider_audit_payload=tampered_audit,
    )
    valid_bad_audit, checks_bad_audit = verify_evidence_package(package_bad_audit)
    assert valid_bad_audit is False
    assert checks_bad_audit.get("hashes", "") == "FAIL: Provider audit hash mismatch"

    # Tampering C': request payload does not match its claimed hash.
    package_bad_req = build_evidence_package(
        envelope,
        request_payload={"grace_period_seconds": 99},
        provider_audit_payload=provider_audit,
    )
    valid_bad_req, checks_bad_req = verify_evidence_package(package_bad_req)
    assert valid_bad_req is False
    assert checks_bad_req.get("hashes", "") == "FAIL: Request hash mismatch"

    # Tampering D (P1.6): provider_action_id in the audit payload diverges from
    # the envelope's execution block. Re-sign a forged envelope whose audit hash
    # matches the tampered payload so the linkage cross-check is what catches it.
    mismatched_audit = dict(provider_audit)
    mismatched_audit["provider_action_id"] = "morph-task-99999999"

    forged_env = copy.deepcopy(envelope)
    ev_d = forged_env.pop("evidence")
    ev_d["hashes"]["provider_audit"] = sha256_hex(canonical_json_bytes(mismatched_audit))
    payload_to_sign_d = {k: v for k, v in forged_env.items()}
    payload_to_sign_d["evidence_hashes"] = ev_d["hashes"]
    forged_env["evidence"] = ev_d
    forged_env["evidence"]["signature"] = engine.signer.sign_payload(payload_to_sign_d)

    package_mismatch = build_evidence_package(
        forged_env,
        request_payload={},
        provider_audit_payload=mismatched_audit,
    )
    valid_mismatch, checks_mismatch = verify_evidence_package(package_mismatch)
    assert valid_mismatch is False
    assert checks_mismatch.get("provider_linkage", "") == "FAIL: Provider audit payload does not bind to provider_action_id"
