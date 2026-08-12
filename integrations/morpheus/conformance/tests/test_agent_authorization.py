"""MOR-002: Agent authorization.

Authorization mirrors Morpheus RBAC into capability URIs: an agent may act only
for capabilities granted to it, and a denied capability never reaches Morpheus.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC

pytestmark = pytest.mark.level("L3")


def test_ungranted_capability_is_denied(client, make_request, quota):
    decision = client.govern(
        make_request(COMPLIANT_SPEC, capability="capability://storage/delete"), quota=quota
    )
    assert decision.decision == "DENY"
    assert decision.reason == "CAPABILITY_VIOLATION"
    assert not decision.morpheus_called


def test_granted_capability_via_role_is_allowed(client, make_request, quota):
    decision = client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    assert decision.decision == "ALLOW"
    assert any(c["check"] == "capability" and c["result"] == "PASS" for c in decision.checks)


def test_authorize_reports_reason(capabilities):
    ok, reason = capabilities.authorize("agent://ml-platform", "capability://compute/provision")
    assert ok
    assert "grant" in reason
