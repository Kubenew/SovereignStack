"""
OASA Policy and Authorization Adapter for AWS Neuron Accelerators.
Specification: OASA v0.6 Governed Autonomous Action / RFC-0075.
"""

from typing import Dict, Any, Optional, List


class NeuronAuthorizationError(PermissionError):
    """Raised when an accelerator operation violates OASA policy."""
    pass


class NeuronPolicyAdapter:
    """
    Gates AWS Neuron operations behind SovereignStack OASA policy evaluation.
    Enforces the Anti-Theater invariant: unauthorized actions are halted
    before touching accelerator hardware.
    """

    ALLOWED_OPERATIONS = {
        "accelerator:neuron:load",
        "accelerator:neuron:compile",
        "accelerator:neuron:trace",
        "accelerator:neuron:infer",
        "accelerator:neuron:artifact_export",
    }

    def __init__(self, policy_rules: Optional[Dict[str, Any]] = None):
        self.policy_rules = policy_rules or {}
        self.authorization_log: List[Dict[str, Any]] = []

    def authorize(
        self,
        operation: str,
        identity_uri: str = "agent://default",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an action against OASA policy.
        Returns authorization decision envelope.
        """
        context = context or {}

        if operation not in self.ALLOWED_OPERATIONS:
            decision = {
                "decision": "deny",
                "operation": operation,
                "identity_uri": identity_uri,
                "reason": f"Unknown or disallowed accelerator operation: {operation}",
                "policy_ref": "policy://accelerator/deny-unknown",
            }
            self.authorization_log.append(decision)
            raise NeuronAuthorizationError(decision["reason"])

        # Check explicit denial flags in context
        if context.get("restricted", False) or context.get("deny_accelerator", False):
            decision = {
                "decision": "deny",
                "operation": operation,
                "identity_uri": identity_uri,
                "reason": "Explicit restriction tag on workload context",
                "policy_ref": "policy://accelerator/context-restriction",
            }
            self.authorization_log.append(decision)
            raise NeuronAuthorizationError(decision["reason"])

        # Validate air-gapped / network egress constraints if compilation or trace
        if operation in ("accelerator:neuron:compile", "accelerator:neuron:trace"):
            if context.get("allow_wan", False):
                decision = {
                    "decision": "deny",
                    "operation": operation,
                    "identity_uri": identity_uri,
                    "reason": "Compilation requires strictly air-gapped environment (WAN disallowed)",
                    "policy_ref": "policy://accelerator/airgap-enforcement",
                }
                self.authorization_log.append(decision)
                raise NeuronAuthorizationError(decision["reason"])

        decision = {
            "decision": "allow",
            "operation": operation,
            "identity_uri": identity_uri,
            "policy_ref": f"policy://accelerator/neuron/{operation.replace(':', '/')}",
            "context_summary": {k: v for k, v in context.items() if k != "weights"},
        }
        self.authorization_log.append(decision)
        return decision

