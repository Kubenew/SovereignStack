"""
SovereignStack Model Context Protocol (MCP) Integration
Provides a bidirectional, governed interoperability layer for AI agents:
1. Expose SovereignStack's OASA Golden Path to AI clients via FastMCP.
2. Proxy & govern external MCP tool execution via GovernedMCPClient.
"""

from integrations.mcp.contracts import (
    OASAService,
    UnconfiguredOASAService,
    CoreEngineOASAAdapter,
)
from integrations.mcp.server import (
    mcp,
    set_oasa_service,
    get_oasa_service,
    set_current_principal,
    resolve_principal,
)
from integrations.mcp.client import GovernedMCPClient

__all__ = [
    "mcp",
    "OASAService",
    "UnconfiguredOASAService",
    "CoreEngineOASAAdapter",
    "GovernedMCPClient",
    "set_oasa_service",
    "get_oasa_service",
    "set_current_principal",
    "resolve_principal",
]
