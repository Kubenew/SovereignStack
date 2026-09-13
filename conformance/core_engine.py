"""
OASA v0.6 Core Engine & Vendor-Neutral Governance Plane
Specification: OASA v0.6 Governed Autonomous Action
"""

import uuid
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse

from conformance.action_envelope import (
    TokenStateStore,
    EnvelopeSigner,
    ActionEnvelopeBuilder,
)


class CoreEngine:
    """
    SovereignStack OASA Core Engine.
    Implements the 5 Golden Path verbs:
    1. discover
    2. authorize
    3. execute (dispatches via target://scheme to registered adapters)
    4. record
    5. verify (stateless independent verifier)
    """

    def __init__(self, signer: Optional[EnvelopeSigner] = None):
        self.signer = signer or EnvelopeSigner()
        self.token_store = TokenStateStore()
        self.adapters: Dict[str, Any] = {}
        self.action_registry: Dict[str, Dict[str, Any]] = {}
        self.denial_records: List[Dict[str, Any]] = []

    def register_adapter(self, scheme: str, adapter: Any):
        """Register an execution adapter for a specific URI scheme (e.g., 'morpheus', 'k8s', 'harness')."""
        self.adapters[scheme] = adapter

    def get_adapter_for_target(self, target_uri: str) -> Optional[Any]:
        parsed = urlparse(target_uri)
        scheme = parsed.scheme
        return self.adapters.get(scheme)

    # 1. DISCOVER
    def discover(self, actor_id: str, target_uri: str) -> Dict[str, Any]:
        adapter = self.get_adapter_for_target(target_uri)
        if not adapter:
            return {
                "status": "FAIL",
                "error": f"No adapter registered for scheme: {urlparse(target_uri).scheme}",
                "targets": [],
            }
        targets = adapter.discover(actor_id, target_uri)
        return {
            "status": "SUCCESS",
            "supported_schemes": list(self.adapters.keys()),
            "targets": targets,
        }

    # 2. AUTHORIZE
    def authorize(
        self,
        actor_id: str,
        actor_type: str,
        capability_id: str,
        target_uri: str,
        delegation: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 300,
    ) -> Dict[str, Any]:
        action_id = f"act_{uuid.uuid4().hex[:16]}"
        delegation_chain = delegation or []

        # --- Policy Evaluation (Fail-Closed) ---
        # 1. Reject unknown or dangerous operations
        # Support-bot or non-admin cannot perform destructive operations or delete production
        is_denied = False
        denial_reason = ""

        # Check explicit rules
        if "delete" in capability_id.lower() or "delete" in target_uri.lower():
            is_denied = True
            denial_reason = "Policy violation: destructive actions strictly prohibited for actor"
        elif "production" in target_uri.lower() and "admin" not in actor_id.lower():
            is_denied = True
            denial_reason = "Policy violation: non-admin actor cannot modify production targets"
        elif capability_id not in [
            "infrastructure.vm.restart",
            "infrastructure.vm.status",
            "infrastructure.vm.provision",
        ]:
            is_denied = True
            denial_reason = f"Policy violation: capability '{capability_id}' not granted"

        # Check delegation chain integrity
        for link in delegation_chain:
            if not (link.startswith("human://") or link.startswith("agent://")):
                is_denied = True
                denial_reason = f"Invalid delegation link format: {link}"
                break

        if is_denied:
            # Create a Denial Action Envelope
            envelope = ActionEnvelopeBuilder.create_envelope(
                action_id=action_id,
                actor_id=actor_id,
                actor_type=actor_type,
                capability_id=capability_id,
                target_uri=target_uri,
                decision="deny",
                delegation=delegation_chain,
                policy_id="policy-production-safety-v1",
                request_payload=parameters or {},
                signer=self.signer,
                reason=denial_reason,
            )
            self.denial_records.append(envelope)
            self.action_registry[action_id] = envelope
            return {
                "decision": "deny",
                "action_id": action_id,
                "reason": denial_reason,
                "envelope": envelope,
            }

        # Issue single-use authorization token
        token_id = f"tok_{uuid.uuid4().hex[:16]}"
        token_record = self.token_store.issue_token(
            token_id=token_id,
            actor_id=actor_id,
            action=capability_id,
            target_uri=target_uri,
            ttl_seconds=ttl_seconds,
        )

        envelope = ActionEnvelopeBuilder.create_envelope(
            action_id=action_id,
            actor_id=actor_id,
            actor_type=actor_type,
            capability_id=capability_id,
            target_uri=target_uri,
            decision="allow",
            token_id=token_id,
            delegation=delegation_chain,
            policy_id="policy-production-safety-v1",
            request_payload=parameters or {},
            signer=self.signer,
            reason="Authorized under production safety policy",
        )
        self.action_registry[action_id] = envelope

        return {
            "decision": "allow",
            "action_id": action_id,
            "token_id": token_id,
            "expires_at": token_record["expires_at"],
            "envelope": envelope,
        }

    # 3. EXECUTE
    def execute(
        self,
        action_id: str,
        token_id: str,
        presenting_actor_id: str,
        target_uri: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an authorized action.
        1. Atomic token consumption.
        2. Adapter resolution via target://scheme.
        3. Dispatch to adapter.
        """
        if action_id not in self.action_registry:
            return {"status": "FAIL", "error": "ACTION_NOT_FOUND"}

        envelope = self.action_registry[action_id]
        if envelope.get("authorization", {}).get("decision") != "allow":
            return {"status": "FAIL", "error": "CANNOT_EXECUTE_DENIED_ACTION"}

        # Atomic token check & consume
        success, reason = self.token_store.consume_token(
            token_id=token_id,
            presenting_actor_id=presenting_actor_id,
            target_uri=target_uri,
        )
        if not success:
            return {"status": "FAIL", "error": reason}

        # Resolve adapter
        adapter = self.get_adapter_for_target(target_uri)
        if not adapter:
            return {"status": "FAIL", "error": "NO_ADAPTER_FOR_SCHEME"}

        # Dispatch execution to adapter
        try:
            exec_result = adapter.execute(envelope)
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}

        # Ingest provider execution
        provider_audit = adapter.record(envelope, exec_result)

        # Update envelope with execution & provider audit
        updated_envelope = ActionEnvelopeBuilder.create_envelope(
            action_id=envelope["action_id"],
            actor_id=envelope["actor"]["id"],
            actor_type=envelope["actor"]["type"],
            capability_id=envelope["capability"]["id"],
            target_uri=envelope["target"]["uri"],
            decision="allow",
            token_id=token_id,
            delegation=envelope.get("delegation"),
            policy_id=envelope.get("policy", {}).get("id"),
            provider=exec_result.get("provider"),
            provider_action_id=exec_result.get("provider_action_id"),
            request_payload=payload or {},
            provider_audit_payload=provider_audit,
            signer=self.signer,
        )
        self.action_registry[action_id] = updated_envelope

        return {
            "status": "SUCCESS",
            "action_id": action_id,
            "provider_action_id": exec_result.get("provider_action_id"),
            "envelope": updated_envelope,
            "provider_audit": provider_audit,
        }

    # 4. RECORD
    def record(self, action_id: str) -> Optional[Dict[str, Any]]:
        return self.action_registry.get(action_id)

    # 5. VERIFY
    @staticmethod
    def verify(envelope: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        return ActionEnvelopeBuilder.verify_envelope(envelope)
