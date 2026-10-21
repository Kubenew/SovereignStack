"""
SovereignStack Governed MCP Client
Consumes third-party MCP servers as governed tools under SovereignStack OASA policy,
providing the reverse direction of the MCP interoperability layer.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional
from integrations.mcp.contracts import OASAService, UnconfiguredOASAService

logger = logging.getLogger(__name__)


class GovernedMCPClient:
    """
    Governed MCP Client proxy.
    Wraps tool invocations to third-party MCP servers with SovereignStack OASA Governance:
    1. Pre-action Policy Gate: Checks authorization before allowing the tool to execute.
    2. Anti-Theater Enforcement: Denied tools are never called.
    3. Provenance & Cryptographic Binding: Successful executions produce verified Action Envelopes.
    4. Kill-Switch Compliance: Enforces immediate revocation if emergency stop is triggered.
    """

    def __init__(
        self,
        oasa_service: Optional[OASAService] = None,
        principal: str = "agent://mcp-orchestrator",
        target_uri_prefix: str = "mcp://tools",
    ):
        self.oasa = oasa_service or UnconfiguredOASAService()
        self.principal = principal
        self.target_uri_prefix = target_uri_prefix.rstrip("/")
        self._registered_tools: Dict[str, Callable[..., Any]] = {}
        self.call_count: Dict[str, int] = {}
        self.kill_switch_active = False

    def register_tool(
        self,
        tool_name: str,
        handler: Callable[..., Any],
        capability_id: Optional[str] = None,
        target_uri: Optional[str] = None,
    ) -> None:
        """Register a third-party MCP tool under OASA governance."""
        self._registered_tools[tool_name] = {
            "handler": handler,
            "capability_id": capability_id or f"infrastructure.vm.{tool_name}",
            "target_uri": target_uri or f"{self.target_uri_prefix}/{tool_name}",
        }
        self.call_count[tool_name] = 0

    def list_governed_tools(self) -> List[str]:
        """Return all registered MCP tools under governance."""
        return list(self._registered_tools.keys())

    def trigger_kill_switch(self) -> None:
        """Activate the emergency kill switch, blocking all downstream tool execution."""
        self.kill_switch_active = True

    def reset_kill_switch(self) -> None:
        """Reset emergency kill switch."""
        self.kill_switch_active = False

    def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        delegation: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool under strict OASA governance.
        """
        args = arguments or {}

        # 0. Kill switch check
        if self.kill_switch_active:
            return {
                "status": "DENIED",
                "decision": "DENY",
                "reason": "KILL_SWITCH_ACTIVE: Autonomous execution suspended by governance plane.",
                "tool_calls_made": 0,
            }

        # Verify tool is registered
        if tool_name not in self._registered_tools:
            return {
                "status": "FAIL",
                "error": f"Tool '{tool_name}' not registered in governed client.",
                "tool_calls_made": 0,
            }

        tool_meta = self._registered_tools[tool_name]
        target_uri = tool_meta["target_uri"]
        capability_id = tool_meta["capability_id"]

        # 1. DISCOVER / PRE-ACTION AUTHORIZE
        auth_result = self.oasa.evaluate_action(
            principal=self.principal,
            capability_id=capability_id,
            target_uri=target_uri,
            parameters=args,
            delegation=delegation or [],
        )

        decision = auth_result.get("decision", "DENY").upper()
        if decision != "ALLOW":
            # ANTI-THEATER GUARANTEE: Zero calls to handler on denial
            return {
                "status": "DENIED",
                "decision": "DENY",
                "action_id": auth_result.get("action_id"),
                "reason": auth_result.get("reason", "Policy violation"),
                "tool_calls_made": 0,
            }

        # 2. EXECUTE THROUGH GOVERNED RUNTIME
        handler = tool_meta["handler"]
        try:
            self.call_count[tool_name] += 1
            result = handler(**args)
            execution_status = "SUCCESS"
        except Exception as e:
            result = {"error": str(e)}
            execution_status = "FAIL"

        # 3. RECORD PROVENANCE & COMPLETE ENVELOPE
        action_id = auth_result.get("action_id", "")
        token_id = auth_result.get("token_id", "")
        exec_record = self.oasa.execute_action(
            principal=self.principal,
            action_id=action_id,
            token_id=token_id,
            target_uri=target_uri,
            payload=args,
        )

        return {
            "status": execution_status,
            "decision": "ALLOW",
            "action_id": action_id,
            "result": result,
            "governance_record": exec_record,
            "tool_calls_made": 1,
        }
