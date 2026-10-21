"""
Security tests verifying fail-closed invariants for SovereignStack MCP integration.
"""

import pytest
from integrations.mcp.contracts import UnconfiguredOASAService
from integrations.mcp.server import resolve_principal, set_current_principal


def test_unconfigured_service_never_authorizes():
    """Unconfigured bootstrap service must fail closed on evaluation."""
    service = UnconfiguredOASAService()
    result = service.evaluate_action(
        principal="agent://untrusted",
        capability_id="infrastructure.vm.restart",
        target_uri="morpheus://vm/staging-web-01",
    )
    assert result["authorized"] is False
    assert result["allowed"] is False
    assert result["decision"] == "NOT_EVALUATED"


def test_unconfigured_discovery_grants_no_capabilities():
    """Unconfigured service must yield empty discovery."""
    service = UnconfiguredOASAService()
    result = service.discover(principal="agent://test")
    assert result["capabilities"] == []
    assert result["targets"] == []
    assert result["status"] == "core_not_configured"


def test_unconfigured_verifier_never_claims_success():
    """Unconfigured verifier must reject evidence verification."""
    service = UnconfiguredOASAService()
    result = service.verify_evidence({"signature": "untrusted"})
    assert result["verified"] is False
    assert result["status"] == "FAIL"


def test_unconfigured_execution_is_blocked():
    """Unconfigured service must reject any execution attempts."""
    service = UnconfiguredOASAService()
    result = service.execute_action(
        principal="agent://test",
        action_id="act_fake123",
        token_id="tok_fake123",
        target_uri="morpheus://vm/staging-web-01",
    )
    assert result["status"] == "FAIL"
    assert "CORE_NOT_CONFIGURED" in result["error"]


def test_missing_principal_fails_closed():
    """Missing authentication must raise PermissionError without trusting client."""
    set_current_principal(None)
    with pytest.raises(PermissionError, match="Authentication is not configured"):
        resolve_principal()
