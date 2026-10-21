"""
OASA Integration Contracts for Model Context Protocol (MCP)
Specification: SovereignStack MCP Gateway & Interoperability Layer
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple

logger = logging.getLogger(__name__)


class OASAService(Protocol):
    """
    Adapter boundary between Model Context Protocol (MCP) and SovereignStack OASA Core.
    Guarantees that MCP transports requests while SovereignStack strictly controls:
    - DISCOVER: Capability & target scoping
    - AUTHORIZE: SIRA policy evaluation & single-use atomic lease issuance
    - EXECUTE: Adapter dispatch via target://scheme
    - RECORD: Cryptographic action envelopes & provenance
    - VERIFY: Stateless independent evidence verification
    """

    def get_status(self) -> Dict[str, Any]:
        """Return gateway and governance health status."""
        ...

    def discover(self, principal: str, target_uri: str = "morpheus://vm/*") -> Dict[str, Any]:
        """Return capabilities and target resources authorized for the caller."""
        ...

    def evaluate_action(
        self,
        principal: str,
        capability_id: str,
        target_uri: str,
        parameters: Optional[Dict[str, Any]] = None,
        delegation: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an action against OASA policies without executing it.
        Returns authorization decision (allow/deny), action_id, single-use token (if allowed),
        and cryptographic action envelope.
        """
        ...

    def execute_action(
        self,
        principal: str,
        action_id: str,
        token_id: str,
        target_uri: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an authorized action by presenting the single-use token to the execution plane.
        Guarantees that denied or unauthenticated actions never reach execution backends.
        """
        ...

    def get_action(self, principal: str, action_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an action envelope by action_id."""
        ...

    def get_provenance(self, principal: str, action_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the immutable provenance and audit record for an action."""
        ...

    def verify_evidence(
        self,
        evidence: Dict[str, Any],
        request_payload: Optional[Dict[str, Any]] = None,
        provider_audit_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke the independent cryptographic verifier on an OASA Action Envelope
        or evidence package.
        """
        ...

    def request_human_approval(
        self,
        principal: str,
        action_id: str,
        justification: str,
    ) -> Dict[str, Any]:
        """Submit a sensitive action to the human override / approval workflow."""
        ...


class UnconfiguredOASAService:
    """
    Safe bootstrap implementation of OASAService.
    Fail-closed: Never authorizes execution, returns empty discovery,
    and rejects verification claims.
    """

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "SovereignStack MCP",
            "adapter_status": "running",
            "core_status": "not_configured",
            "governance_mode": "FAIL_CLOSED",
        }

    def discover(self, principal: str, target_uri: str = "morpheus://vm/*") -> Dict[str, Any]:
        return {
            "principal": principal,
            "capabilities": [],
            "targets": [],
            "status": "core_not_configured",
        }

    def evaluate_action(
        self,
        principal: str,
        capability_id: str,
        target_uri: str,
        parameters: Optional[Dict[str, Any]] = None,
        delegation: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return {
            "decision": "NOT_EVALUATED",
            "authorized": False,
            "allowed": False,
            "reason": "Policy engine integration is not configured.",
            "principal": principal,
            "capability_id": capability_id,
            "target_uri": target_uri,
        }

    def execute_action(
        self,
        principal: str,
        action_id: str,
        token_id: str,
        target_uri: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "status": "FAIL",
            "error": "CORE_NOT_CONFIGURED: Execution disabled until OASA core is connected.",
        }

    def get_action(self, principal: str, action_id: str) -> Optional[Dict[str, Any]]:
        return None

    def get_provenance(self, principal: str, action_id: str) -> Optional[Dict[str, Any]]:
        return None

    def verify_evidence(
        self,
        evidence: Dict[str, Any],
        request_payload: Optional[Dict[str, Any]] = None,
        provider_audit_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "verified": False,
            "status": "FAIL",
            "reason": "Cryptographic verifier is not configured.",
        }

    def request_human_approval(
        self,
        principal: str,
        action_id: str,
        justification: str,
    ) -> Dict[str, Any]:
        return {
            "status": "DENIED",
            "reason": "Human approval workflow backend is not configured.",
            "action_id": action_id,
        }


class CoreEngineOASAAdapter:
    """
    Production adapter bridging the MCP Gateway directly into SovereignStack's
    CoreEngine and registered execution adapters (Morpheus, K8s, etc.).
    """

    def __init__(self, core_engine: Any = None):
        if core_engine is None:
            from conformance.core_engine import CoreEngine
            from integrations.morpheus.adapter.morpheus_adapter import MorpheusAdapter

            self.engine = CoreEngine()
            # Register reference adapter for morpheus:// targets
            morpheus = MorpheusAdapter(execution_mode="fixture")
            self.engine.register_adapter(morpheus.SCHEME, morpheus)
        else:
            self.engine = core_engine

        self.human_approvals: Dict[str, Dict[str, Any]] = {}

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "SovereignStack MCP Gateway",
            "adapter_status": "running",
            "core_status": "connected",
            "governance_mode": "STRICT_ENFORCEMENT",
            "supported_schemes": list(self.engine.adapters.keys()),
            "registered_actions_count": len(self.engine.action_registry),
        }

    def discover(self, principal: str, target_uri: str = "morpheus://vm/*") -> Dict[str, Any]:
        result = self.engine.discover(actor_id=principal, target_uri=target_uri)
        return {
            "principal": principal,
            "target_uri": target_uri,
            "status": result.get("status", "FAIL"),
            "targets": result.get("targets", []),
            "supported_schemes": result.get("supported_schemes", []),
        }

    def evaluate_action(
        self,
        principal: str,
        capability_id: str,
        target_uri: str,
        parameters: Optional[Dict[str, Any]] = None,
        delegation: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        auth_result = self.engine.authorize(
            actor_id=principal,
            actor_type="agent",
            capability_id=capability_id,
            target_uri=target_uri,
            delegation=delegation or [],
            parameters=parameters or {},
        )
        decision = auth_result.get("decision", "deny")
        return {
            "decision": decision.upper(),
            "allowed": (decision == "allow"),
            "authorized": (decision == "allow"),
            "action_id": auth_result.get("action_id"),
            "token_id": auth_result.get("token_id"),
            "expires_at": auth_result.get("expires_at"),
            "reason": auth_result.get("reason"),
            "envelope": auth_result.get("envelope"),
        }

    def execute_action(
        self,
        principal: str,
        action_id: str,
        token_id: str,
        target_uri: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        exec_result = self.engine.execute(
            action_id=action_id,
            token_id=token_id,
            presenting_actor_id=principal,
            target_uri=target_uri,
            payload=payload or {},
        )
        return exec_result

    def get_action(self, principal: str, action_id: str) -> Optional[Dict[str, Any]]:
        return self.engine.record(action_id)

    def get_provenance(self, principal: str, action_id: str) -> Optional[Dict[str, Any]]:
        envelope = self.engine.record(action_id)
        if not envelope:
            return None
        return {
            "action_id": action_id,
            "provenance": envelope.get("evidence", {}),
            "authorization": envelope.get("authorization", {}),
            "execution": envelope.get("execution", {}),
        }

    def verify_evidence(
        self,
        evidence: Dict[str, Any],
        request_payload: Optional[Dict[str, Any]] = None,
        provider_audit_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        envelope = evidence.get("envelope", evidence)
        valid, checks = self.engine.verify(
            envelope=envelope,
            request_payload=request_payload,
            provider_audit_payload=provider_audit_payload,
        )
        return {
            "verified": valid,
            "status": "PASS" if valid else "FAIL",
            "checks": checks,
        }

    def request_human_approval(
        self,
        principal: str,
        action_id: str,
        justification: str,
    ) -> Dict[str, Any]:
        self.human_approvals[action_id] = {
            "principal": principal,
            "action_id": action_id,
            "justification": justification,
            "status": "PENDING_REVIEW",
        }
        return {
            "status": "PENDING_REVIEW",
            "action_id": action_id,
            "message": f"Action {action_id} submitted to human supervisor for review.",
        }
