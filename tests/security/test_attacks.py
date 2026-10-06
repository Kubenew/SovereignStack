import pytest
import requests
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from conformance.core_engine import CoreEngine
from conformance.action_envelope import (
    canonical_json_bytes,
    sha256_hex,
)
from integrations.morpheus.adapter.morpheus_adapter import MorpheusAdapter

API_BASE = "http://localhost:8546"

def is_node_up():
    try:
        return requests.get(f"{API_BASE}/sip/v1/ping", timeout=1).status_code == 200
    except Exception:
        return False


def test_forged_identity():
    # Verify that an identity with forged signature fails cryptographic verification
    key_alice = ed25519.Ed25519PrivateKey.generate()
    key_eve = ed25519.Ed25519PrivateKey.generate()
    
    payload = b"identity-did:sov:alice"
    signature_alice = key_alice.sign(payload)
    
    with pytest.raises(InvalidSignature):
        key_eve.public_key().verify(signature_alice, payload)


def test_invalid_signature():
    # Verify that tampered payload fails signature verification
    key = ed25519.Ed25519PrivateKey.generate()
    payload = b"sovereign-object-canonical-state"
    signature = key.sign(payload)
    
    tampered_payload = b"sovereign-object-tampered-state"
    with pytest.raises(InvalidSignature):
        key.public_key().verify(signature, tampered_payload)


def test_replayed_capability():
    # CoreEngine: Attempting to reuse an authorization token a second time must fail
    engine = CoreEngine()
    adapter = MorpheusAdapter()
    engine.register_adapter("morpheus", adapter)
    
    auth = engine.authorize("agent://ops-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    action_id = auth["action_id"]
    token_id = auth["token_id"]
    
    # First execution succeeds
    res1 = engine.execute(action_id, token_id, "agent://ops-bot", "morpheus://vm/staging-web-01")
    assert res1["status"] == "SUCCESS"
    
    # Replay with same token fails
    res2 = engine.execute(action_id, token_id, "agent://ops-bot", "morpheus://vm/staging-web-01")
    assert res2["status"] == "FAIL"


def test_expired_capability():
    # Non-existent or expired token fails execution
    engine = CoreEngine()
    res = engine.execute("act_none", "tok_expired_nonexistent", "agent://ops-bot", "morpheus://vm/staging-web-01")
    assert res["status"] == "FAIL"


def test_capability_escalation():
    # Agent requesting unauthorized capability is denied
    engine = CoreEngine()
    auth = engine.authorize(
        actor_id="agent://untrusted-guest",
        actor_type="agent",
        capability_id="system.root.privilege_escalation",
        target_uri="morpheus://vm/production-db",
    )
    assert auth["decision"] == "deny"


def test_policy_bypass():
    # Default policy must deny arbitrary actors trying destructive actions on production
    engine = CoreEngine()
    auth = engine.authorize(
        actor_id="agent://customer-support-bot",
        actor_type="agent",
        capability_id="infrastructure.vm.delete",
        target_uri="morpheus://vm/prod-db-cluster",
    )
    assert auth["decision"] == "deny"


def test_provenance_tampering():
    # Tampering with provenance hashes or envelope fields must fail verification
    engine = CoreEngine()
    adapter = MorpheusAdapter()
    engine.register_adapter("morpheus", adapter)
    
    auth = engine.authorize("agent://ops-bot", "agent", "infrastructure.vm.restart", "morpheus://vm/staging-web-01")
    exec_res = engine.execute(auth["action_id"], auth["token_id"], "agent://ops-bot", "morpheus://vm/staging-web-01")
    envelope = exec_res["envelope"]
    
    # Tamper with target uri
    tampered_envelope = dict(envelope)
    tampered_envelope["target"] = {"uri": "morpheus://vm/tampered-target"}
    
    valid, _ = CoreEngine.verify(tampered_envelope)
    assert valid is False


def test_event_modification():
    # Modifying event data changes canonical hash
    data_1 = {"event": "state_change", "version": 1}
    data_2 = {"event": "state_change", "version": 2}
    hash_1 = sha256_hex(canonical_json_bytes(data_1))
    hash_2 = sha256_hex(canonical_json_bytes(data_2))
    assert hash_1 != hash_2


def test_unauthorized_mutation():
    # Mutating resource without prior authorization must be blocked
    engine = CoreEngine()
    res = engine.execute(
        action_id="act_unauthorized_mutate",
        token_id="tok_invalid",
        presenting_actor_id="agent://attacker",
        target_uri="morpheus://vm/cluster",
    )
    assert res["status"] == "FAIL"


def test_invalid_delegation():
    # Malformed delegation links must be rejected
    engine = CoreEngine()
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

