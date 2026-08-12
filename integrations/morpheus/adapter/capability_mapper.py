"""Capability mapping — Morpheus roles to SovereignStack capability URIs.

A capability grant is the cryptographic counterpart of Morpheus RBAC: an agent
may act on Morpheus only for capabilities that have been granted to it, and the
grant is part of the audited context for every action.
"""

from __future__ import annotations

from typing import Optional

DEFAULT_ROLES = {
    "infra-admin": [
        "capability://compute/provision",
        "capability://compute/configure",
        "capability://storage/configure",
        "capability://network/configure",
    ],
    "ml-engineer": [
        "capability://compute/provision",
        "capability://compute/read",
        "capability://storage/read",
    ],
    "auditor": ["capability://audit/read"],
}


class CapabilityMapper:
    def __init__(self, roles: Optional[dict] = None) -> None:
        self._roles = roles if roles is not None else DEFAULT_ROLES
        self._grants: dict[str, set] = {}
        self._delegation: dict[str, dict] = {}

    def grant(self, agent_uri: str, capability: str) -> None:
        self._grants.setdefault(agent_uri, set()).add(capability)

    def revoke(self, agent_uri: str, capability: str) -> None:
        self._grants.get(agent_uri, set()).discard(capability)

    def grant_role(self, agent_uri: str, role: str) -> None:
        for capability in self._roles.get(role, []):
            self._grants.setdefault(agent_uri, set()).add(capability)

    def delegate(self, agent_uri: str, capability: str, delegated_by: str) -> None:
        """Record a human-authority delegation (RFC-0026 pattern).

        ``delegated_by`` is typically ``human://<owner>`` or a signed authority
        statement. The delegation is recorded so the evidence chain can show
        *why* the agent was allowed to act.
        """
        self.grant(agent_uri, capability)
        self._delegation[(agent_uri, capability)] = {"delegated_by": delegated_by}

    def delegation_evidence(self, agent_uri: str, capability: str) -> Optional[dict]:
        return self._delegation.get((agent_uri, capability))

    def has(self, agent_uri: str, capability: str) -> bool:
        return capability in self._grants.get(agent_uri, set())

    def capabilities(self, agent_uri: str) -> list:
        return sorted(self._grants.get(agent_uri, set()))

    def authorize(self, agent_uri: str, capability: str) -> tuple[bool, str]:
        """Check authorization. Returns ``(allowed, reason)``."""
        if not self.has(agent_uri, capability):
            return False, f"capability {capability} not granted to {agent_uri}"
        delegation = self.delegation_evidence(agent_uri, capability)
        if delegation is None:
            return True, f"direct grant: {capability}"
        return (
            True,
            f"delegated {capability} by {delegation['delegated_by']}",
        )
