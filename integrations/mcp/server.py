"""
SovereignStack Model Context Protocol (MCP) Server
Exposes governed capabilities, context resources, and approved workflows
to AI clients (Claude, GPT, Astra, Grok, Qwen, local LLMs) via MCP.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

from integrations.mcp.contracts import (
    OASAService,
    UnconfiguredOASAService,
    CoreEngineOASAAdapter,
)

# Initialize FastMCP Server
mcp = FastMCP("SovereignStack OASA")

# Global OASA service instance. Defaults to fail-closed UnconfiguredOASAService
# unless explicitly configured or OASA_MCP_BACKEND=core is set.
_backend_env = os.getenv("OASA_MCP_BACKEND", "unconfigured").lower()
if _backend_env in ("core", "production", "live"):
    _oasa_service: OASAService = CoreEngineOASAAdapter()
else:
    _oasa_service: OASAService = UnconfiguredOASAService()

# Current principal override (for testing or authenticated session context)
_current_principal: Optional[str] = None


def set_oasa_service(service: OASAService) -> None:
    """Set the active OASA service implementation for the MCP server."""
    global _oasa_service
    _oasa_service = service


def get_oasa_service() -> OASAService:
    """Get the active OASA service implementation."""
    return _oasa_service


def set_current_principal(principal: Optional[str]) -> None:
    """Explicitly set authenticated principal for session or testing."""
    global _current_principal
    _current_principal = principal


def resolve_principal() -> str:
    """
    Resolve authenticated principal from transport or trusted session.
    Never accepts an untrusted model-supplied principal as proof of identity.
    Fails closed if authentication is not configured.
    """
    global _current_principal
    if _current_principal:
        return _current_principal

    env_principal = os.getenv("OASA_PRINCIPAL")
    if env_principal:
        return env_principal

    # In strict mode without configured identity, reject
    raise PermissionError("Authentication is not configured: request lacks trusted principal")


# ---------------------------------------------------------------------------
# MCP Tools (Golden Path Verbs)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_status() -> Dict[str, Any]:
    """Return SovereignStack MCP gateway status and OASA governance health."""
    return _oasa_service.get_status()


@mcp.tool()
def discover(target_uri: str = "morpheus://vm/*") -> Dict[str, Any]:
    """
    [DISCOVER] Discover OASA capabilities and target infrastructure available to the caller.
    """
    principal = resolve_principal()
    return _oasa_service.discover(principal=principal, target_uri=target_uri)


@mcp.tool()
def evaluate_action(
    capability_id: str,
    target_uri: str,
    parameters: Optional[Dict[str, Any]] = None,
    delegation: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    [AUTHORIZE] Evaluate a proposed autonomous action against OASA policies without executing it.
    Returns: Decision (ALLOW/DENY), Action ID, and atomic single-use authorization token (if allowed).
    """
    principal = resolve_principal()
    return _oasa_service.evaluate_action(
        principal=principal,
        capability_id=capability_id,
        target_uri=target_uri,
        parameters=parameters or {},
        delegation=delegation or [],
    )


@mcp.tool()
def execute_action(
    action_id: str,
    token_id: str,
    target_uri: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    [EXECUTE] Present an authorization token to execute an authorized action via its target adapter.
    Anti-theater invariant: Denied, replayed, or unauthenticated tokens are halted before provider calls.
    """
    principal = resolve_principal()
    return _oasa_service.execute_action(
        principal=principal,
        action_id=action_id,
        token_id=token_id,
        target_uri=target_uri,
        payload=payload or {},
    )


@mcp.tool()
def get_action(action_id: str) -> Dict[str, Any]:
    """
    [RECORD] Retrieve the cryptographic Action Envelope for an action by action_id.
    """
    principal = resolve_principal()
    action = _oasa_service.get_action(principal=principal, action_id=action_id)
    if action is None:
        return {"status": "NOT_FOUND", "action_id": action_id}
    return {"status": "SUCCESS", "action": action}


@mcp.tool()
def get_provenance(action_id: str) -> Dict[str, Any]:
    """
    [RECORD] Retrieve the immutable execution provenance and audit record for an action.
    """
    principal = resolve_principal()
    prov = _oasa_service.get_provenance(principal=principal, action_id=action_id)
    if prov is None:
        return {"status": "NOT_FOUND", "action_id": action_id}
    return {"status": "SUCCESS", "provenance": prov}


@mcp.tool()
def verify_evidence(
    envelope: Dict[str, Any],
    request_payload: Optional[Dict[str, Any]] = None,
    provider_audit_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    [VERIFY] Mathematically verify an OASA Action Envelope or Evidence Package using
    deterministic-json-v1 and Ed25519 signature validation.
    """
    return _oasa_service.verify_evidence(
        evidence=envelope,
        request_payload=request_payload,
        provider_audit_payload=provider_audit_payload,
    )


@mcp.tool()
def request_human_approval(
    action_id: str,
    justification: str,
) -> Dict[str, Any]:
    """
    [HUMAN OVERRIDE] Submit an action for explicit human supervisor review.
    """
    principal = resolve_principal()
    return _oasa_service.request_human_approval(
        principal=principal,
        action_id=action_id,
        justification=justification,
    )


# ---------------------------------------------------------------------------
# MCP Context Resources
# ---------------------------------------------------------------------------

@mcp.resource("sovereignstack://standards/oasa")
def get_oasa_standard_resource() -> str:
    """Read-only OASA specification standard definition."""
    return (
        "# Open Autonomous System Architecture (OASA) v0.6\n\n"
        "Five Golden Path Verbs:\n"
        "1. DISCOVER: Enumerate verified targets and capability grants\n"
        "2. AUTHORIZE: Evaluate pre-action safety policies; issue single-use lease\n"
        "3. EXECUTE: Present authorization token to dispatch execution to provider adapter\n"
        "4. RECORD: Produce deterministic cryptographically bound Action Envelope\n"
        "5. VERIFY: Third-party independent verification using deterministic-json-v1\n"
    )


@mcp.resource("sovereignstack://policies/core")
def get_core_policy_resource() -> str:
    """Read-only Core Governance safety policy reference."""
    return (
        "policy_id: policy-production-safety-v1\n"
        "rules:\n"
        "  - deny: capability contains 'delete' (anti-theater destructive action block)\n"
        "  - deny: target contains 'production' unless actor has admin role\n"
        "  - require: single-use atomic token\n"
        "  - require: valid delegation link format\n"
    )


@mcp.resource("sovereignstack://actions/{action_id}")
def get_action_resource(action_id: str) -> str:
    """Read-only Action Envelope record for action_id."""
    principal = resolve_principal()
    action = _oasa_service.get_action(principal=principal, action_id=action_id)
    if action is None:
        return json.dumps({"error": "Action not found", "action_id": action_id})
    return json.dumps(action, indent=2)


# ---------------------------------------------------------------------------
# MCP Prompt Templates
# ---------------------------------------------------------------------------

@mcp.prompt()
def governed_deployment_review(service_name: str, environment: str) -> str:
    """Prompt template for reviewing an autonomous deployment under OASA governance."""
    return (
        f"You are the SovereignStack Governance Reviewer evaluating an autonomous action for '{service_name}' "
        f"in environment '{environment}'.\n\n"
        "Please follow the OASA Golden Path:\n"
        "1. Check available capabilities using `oasa.discover`.\n"
        "2. Evaluate safety policy using `oasa.evaluate_action`.\n"
        "3. If allowed, execute only with the issued single-use token.\n"
        "4. If denied or hazardous, report the policy violation and do NOT attempt provider execution.\n"
    )


@mcp.prompt()
def security_audit_review(action_id: str) -> str:
    """Prompt template for auditing the cryptographic evidence of an executed action."""
    return (
        f"Audit cryptographic provenance for action ID '{action_id}'.\n\n"
        "1. Retrieve the Action Envelope using `oasa.get_action`.\n"
        "2. Verify the Ed25519 signature and deterministic-json-v1 hashes with `oasa.verify_evidence`.\n"
        "3. Confirm provider action binding and check for any tampering.\n"
    )


if __name__ == "__main__":
    mcp.run()
