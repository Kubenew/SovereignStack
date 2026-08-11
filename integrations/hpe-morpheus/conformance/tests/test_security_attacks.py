"""Security attack scenarios against the governed pipeline.

Each attack must be detected and rejected: replay, signature substitution,
post-hoc event modification, and capability escalation.
"""

from __future__ import annotations

import uuid

import pytest

from _shared import COMPLIANT_SPEC
from adapter.capability_mapper import CapabilityMapper
from api.morpheus_schemas import GovernedRequest
from crypto import canonical_json, generate_keypair, sign
from evidence.evidence_verifier import EvidenceVerifier
from provenance.morpheus_provenance_chain import ProvenanceChain, resolve_key_from

pytestmark = pytest.mark.level("L3")


def _signed(agent_uri: str, private_key_hex: str, spec: dict, nonce: str) -> GovernedRequest:
    request = GovernedRequest(
        action="provision-vm",
        agent_uri=agent_uri,
        capability="capability://compute/provision",
        spec=spec,
        nonce=nonce,
        environment=spec.get("environment"),
    )
    request.signature = sign(canonical_json(request.message()), private_key_hex)
    return request


def test_replay_detected(client, agent_keys, quota):
    nonce = uuid.uuid4().hex
    first = client.govern(_signed("agent://ml-platform", agent_keys["private"], COMPLIANT_SPEC, nonce), quota=quota)
    assert first.decision == "ALLOW"
    replay = client.govern(_signed("agent://ml-platform", agent_keys["private"], COMPLIANT_SPEC, nonce), quota=quota)
    assert replay.decision == "DENY"
    assert replay.reason == "REPLAY_DETECTED"


def test_signature_substitution_detected(agent_keys, quota):
    """Stealing agent A's signature onto agent B's request must fail identity."""
    from adapter.identity_mapper import IdentityMapper
    from adapter.policy_translator import PolicyEvaluator
    from api.morpheus_mock import make_server
    from api.morpheus_client import GovernedClient
    import threading

    alice_private, alice_public = generate_keypair()
    bob_private, bob_public = generate_keypair()

    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    identity = IdentityMapper()
    identity.register("agent://alice", alice_public)
    identity.register("agent://bob", bob_public)
    capabilities = CapabilityMapper()
    capabilities.grant("agent://alice", "capability://compute/provision")
    capabilities.grant("agent://bob", "capability://compute/provision")
    policies = PolicyEvaluator()

    from provenance.morpheus_provenance_chain import ProvenanceChain

    node_private, node_public = generate_keypair()
    client = GovernedClient(
        f"http://127.0.0.1:{server.server_address[1]}",
        identity,
        capabilities,
        policies,
        ProvenanceChain(target="chain://morpheus/attack"),
        node_private,
        node_public,
    )

    # Alice signs her request; attacker replays that signature onto Bob's request
    alice_request = _signed("agent://alice", alice_private, COMPLIANT_SPEC, uuid.uuid4().hex)
    stolen = _signed("agent://bob", bob_private, COMPLIANT_SPEC, uuid.uuid4().hex)
    stolen.signature = alice_request.signature  # substitution

    decision = client.govern(stolen, quota=None)
    assert decision.decision == "DENY"
    assert decision.reason == "IDENTITY_VIOLATION"
    server.shutdown()


def test_post_hoc_event_modification_detected(agent_keys, node_keys):
    from adapter.event_listener import EventListener

    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    listener = EventListener(node_keys["public"])
    listener.record(
        chain,
        action="deleted",
        object_uri="vm://morpheus/vm-7777",
        detail={"status": "deleted"},
        signer_private_key_hex=node_keys["private"],
    )
    chain.entries[-1].detail["status"] = "running"  # attacker rewrites history
    ok, reasons = chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok is False
    assert any("tampered" in r for r in reasons)


def test_capability_escalation_denied(client, make_request, quota):
    """Requesting a capability outside the grant must never reach Morpheus."""
    decision = client.govern(
        make_request(COMPLIANT_SPEC, capability="capability://admin/everything"), quota=quota
    )
    assert decision.decision == "DENY"
    assert decision.reason == "CAPABILITY_VIOLATION"
    assert not decision.morpheus_called


def test_evidence_package_rejects_substituted_chain(client, make_request, quota, agent_keys, node_keys):
    """Swapping in a chain signed by a different node must fail package verify."""
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    package = client.last_package

    other_private, _ = generate_keypair()
    forged = ProvenanceChain(target="chain://morpheus/forged")
    from provenance.morpheus_provenance_chain import ProvenanceEntry

    forged.append(
        ProvenanceEntry(
            seq=1,
            action="provision-vm",
            agent_uri="agent://ml-platform",
            object_uri="vm://morpheus/vm-forged",
            decision="ALLOW",
            detail={"memory_gb": 32},
        ),
        private_key_hex=other_private,
    )
    package.chain = forged.to_dict()

    ok, reasons = EvidenceVerifier().verify(
        package,
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}),
        node_keys["public"],
    )
    assert ok is False
