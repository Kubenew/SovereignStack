"""MOR-001: Identity binding.

A governed request must be traceable to a registered agent whose signature
verifies over the canonical request message, and to a bound Morpheus identity.
"""

from __future__ import annotations

import uuid

import pytest

from _shared import AGENT_URI, COMPLIANT_SPEC
from api.morpheus_schemas import GovernedRequest
from crypto import canonical_json, generate_keypair, sign

pytestmark = pytest.mark.level("L3")


def _signed(agent_uri: str, private_key_hex: str, spec: dict) -> GovernedRequest:
    request = GovernedRequest(
        action="provision-vm",
        agent_uri=agent_uri,
        capability="capability://compute/provision",
        spec=spec,
        nonce=uuid.uuid4().hex,
        environment=spec.get("environment"),
    )
    request.signature = sign(canonical_json(request.message()), private_key_hex)
    return request


def test_morpheus_user_binds_to_agent(identity):
    assert identity.resolve_agent("ml-service-account") == AGENT_URI


def test_registered_agent_with_valid_signature_is_allowed(client, make_request, quota):
    decision = client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    assert decision.decision == "ALLOW"
    assert any(c["check"] == "identity" and c["result"] == "PASS" for c in decision.checks)


def test_unregistered_agent_is_denied(client, quota):
    private, _ = generate_keypair()
    decision = client.govern(_signed("agent://stranger", private, COMPLIANT_SPEC), quota=quota)
    assert decision.decision == "DENY"
    assert decision.reason == "IDENTITY_VIOLATION"


def test_invalid_signature_is_denied(client, quota):
    private, public = generate_keypair()
    client.identity.register("agent://forged", public)
    request = _signed("agent://forged", private, COMPLIANT_SPEC)
    request.signature = "00" * 64  # corrupt after signing
    decision = client.govern(request, quota=quota)
    assert decision.decision == "DENY"
    assert decision.reason == "IDENTITY_VIOLATION"
    assert any(c["check"] == "identity" and c["result"] == "FAIL" for c in decision.checks)
