"""MOR-003: Capability enforcement.

Capability grants are revocable, and delegations (RFC-0026) must be recorded so
the evidence chain can show why an agent was allowed to act.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC

pytestmark = pytest.mark.level("L3")


def test_grant_then_revoke(capabilities):
    capabilities.grant("agent://revoke-me", "capability://compute/read")
    assert capabilities.has("agent://revoke-me", "capability://compute/read")
    capabilities.revoke("agent://revoke-me", "capability://compute/read")
    assert not capabilities.has("agent://revoke-me", "capability://compute/read")


def test_role_grant_expands_to_capabilities(capabilities):
    caps = capabilities.capabilities("agent://ml-platform")
    assert "capability://compute/provision" in caps
    assert "capability://compute/read" in caps


def test_delegation_is_recorded(capabilities):
    capabilities.delegate(
        "agent://data-pipeline", "capability://storage/read", "human://infra-owner"
    )
    evidence = capabilities.delegation_evidence("agent://data-pipeline", "capability://storage/read")
    assert evidence == {"delegated_by": "human://infra-owner"}
    ok, reason = capabilities.authorize("agent://data-pipeline", "capability://storage/read")
    assert ok
    assert "delegated" in reason


def test_revoked_capability_denied_at_gateway(client, capabilities, make_request, quota):
    capabilities.grant("agent://ml-platform", "capability://storage/configure")
    decision = client.govern(
        make_request(COMPLIANT_SPEC, capability="capability://storage/configure"), quota=quota
    )
    assert decision.decision == "ALLOW"
    capabilities.revoke("agent://ml-platform", "capability://storage/configure")
    decision = client.govern(
        make_request(COMPLIANT_SPEC, capability="capability://storage/configure"), quota=quota
    )
    assert decision.decision == "DENY"
    assert decision.reason == "CAPABILITY_VIOLATION"
