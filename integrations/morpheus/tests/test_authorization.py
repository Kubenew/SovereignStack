import pytest
from integrations.morpheus.adapter.authorization import AuthorizationAdapter

def test_authorization_positive():
    adapter = AuthorizationAdapter()
    result = adapter.authorize(
        identity_uri="agent://morpheus/valid",
        operation="morpheus:provision",
        context={"labels": ["secure"]}
    )
    assert result["decision"] == "allow"

def test_forged_identity():
    # Demonstrating fake agent rejection
    adapter = AuthorizationAdapter()
    result = adapter.authorize(
        identity_uri="agent://morpheus/fake",
        operation="morpheus:provision",
        context={}
    )
    assert result["decision"] == "deny"

def test_policy_violation():
    # Demonstrating a policy violation (e.g., egress not allowed)
    adapter = AuthorizationAdapter()
    result = adapter.authorize(
        identity_uri="agent://morpheus/valid",
        operation="morpheus:network_egress",
        context={}
    )
    assert result["decision"] == "deny"
    assert "Egress not permitted" in result["reason"]
