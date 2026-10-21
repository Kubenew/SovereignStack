"""
Discovery and status tests for SovereignStack MCP integration.
"""

from integrations.mcp.contracts import CoreEngineOASAAdapter
from integrations.mcp.server import (
    discover,
    get_status,
    set_current_principal,
    set_oasa_service,
)


def test_mcp_status_connected():
    """Verify get_status tool reports core connection and supported schemes."""
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    status = get_status()
    assert status["adapter_status"] == "running"
    assert status["core_status"] == "connected"
    assert status["governance_mode"] == "STRICT_ENFORCEMENT"
    assert "morpheus" in status["supported_schemes"]


def test_mcp_discovery_returns_targets():
    """Verify discover tool enumerates authorized targets for authenticated principal."""
    adapter = CoreEngineOASAAdapter()
    set_oasa_service(adapter)
    set_current_principal("agent://devops-bot")

    disc = discover("morpheus://vm/*")
    assert disc["status"] == "SUCCESS"
    assert disc["principal"] == "agent://devops-bot"
    assert len(disc["targets"]) > 0
    target_names = [t["name"] for t in disc["targets"]]
    assert "staging-web-01" in target_names
