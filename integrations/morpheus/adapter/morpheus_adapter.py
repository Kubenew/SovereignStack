"""
OASA Reference Adapter for HPE Morpheus
Specification: OASA v0.6 Governed Autonomous Action
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class MorpheusAdapter:
    """
    Reference Execution Adapter for HPE Morpheus.
    Implements the standard OASA Adapter Interface:
    - Metadata()
    - Discover(req)
    - Execute(action_envelope)
    - Record(execution_result)
    
    Maintains call tracking to verify the Anti-Theater invariant
    (denied actions never call the provider).
    """

    SCHEME = "morpheus"

    def __init__(self, endpoint: str = "https://morpheus.internal.local", live_client: Optional[Any] = None, execution_mode: str = "fixture"):
        self.endpoint = endpoint
        self.live_client = live_client
        self.execution_mode = execution_mode
        self.provider_call_count = 0
        self.executed_actions: Dict[str, Dict[str, Any]] = {}

    def metadata(self) -> Dict[str, Any]:
        return {
            "adapter_id": "adapter.morpheus.v0.6",
            "provider": "hpe-morpheus",
            "supported_schemes": ["morpheus"],
            "supported_actions": [
                "infrastructure.vm.restart",
                "infrastructure.vm.status",
                "infrastructure.vm.provision",
            ],
            "restricted_actions": [
                "infrastructure.vm.delete",
                "infrastructure.network.egress",
            ],
        }

    def discover(self, actor_id: str, target_uri: str) -> List[Dict[str, Any]]:
        """
        Discover available resources matching target_uri.
        """
        return [
            {
                "uri": "morpheus://vm/staging-web-01",
                "name": "staging-web-01",
                "type": "vm",
                "environment": "staging",
                "capabilities": ["infrastructure.vm.restart", "infrastructure.vm.status"],
            },
            {
                "uri": "morpheus://vm/production-db-01",
                "name": "production-db-01",
                "type": "database",
                "environment": "production",
                "capabilities": ["infrastructure.vm.status"],
            },
        ]

    def execute(self, action_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an authorized action against the provider.
        CRITICAL: This MUST ONLY be called after authorization is validated!
        """
        auth = action_envelope.get("authorization", {})
        if auth.get("decision") != "allow":
            raise PermissionError("OASA-MUST-AUTH-002: Cannot execute an unauthorized action envelope.")

        target_uri = action_envelope.get("target", {}).get("uri", "")
        cap_id = action_envelope.get("capability", {}).get("id", "")

        if self.execution_mode == "live":
            raise NotImplementedError("Live execution against Morpheus is not yet configured. Use fixture mode.")

        # Increment provider execution counter
        self.provider_call_count += 1

        provider_action_id = f"morph-task-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        execution_record = {
            "status": "SUCCESS",
            "provider": "morpheus",
            "provider_action_id": provider_action_id,
            "target_uri": target_uri,
            "capability_id": cap_id,
            "executed_at": now_iso,
            "details": {
                "task_name": f"Execute {cap_id} on {target_uri}",
                "exit_code": 0,
                "message": "Operation completed successfully by Morpheus provider engine",
            },
        }

        self.executed_actions[action_envelope["action_id"]] = execution_record
        return execution_record

    def record(self, action_envelope: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce native provider audit evidence linked to the OASA action.
        """
        return {
            "provider": "hpe-morpheus",
            "provider_action_id": execution_result["provider_action_id"],
            "oasa_action_id": action_envelope["action_id"],
            "timestamp": execution_result["executed_at"],
            "audit_event": {
                "event_type": "WORKLOAD_STATE_CHANGE",
                "actor": action_envelope.get("actor", {}).get("id"),
                "target": execution_result["target_uri"],
                "provider_audit_log_id": f"morpheus-audit-{uuid.uuid4().hex[:12]}",
                "status": execution_result["status"],
            },
        }
