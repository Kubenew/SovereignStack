"""Shared API types and canonical serialization for the Morpheus integration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj) -> bytes:
    """Deterministic canonical JSON (sorted keys, compact separators)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass
class GovernedRequest:
    """A signed agent request submitted for governance."""

    action: str
    agent_uri: str
    capability: str
    spec: dict
    nonce: str
    environment: Optional[str] = None
    ts: str = field(default_factory=now_iso)
    signature: Optional[str] = None

    def message(self) -> dict:
        """The canonical message an agent signs."""
        return {
            "action": self.action,
            "agent_uri": self.agent_uri,
            "capability": self.capability,
            "spec": self.spec,
            "nonce": self.nonce,
            "environment": self.environment,
        }

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "agent_uri": self.agent_uri,
            "capability": self.capability,
            "spec": self.spec,
            "nonce": self.nonce,
            "environment": self.environment,
            "ts": self.ts,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GovernedRequest":
        return cls(**data)


@dataclass
class GovernedDecision:
    """The outcome of the governance pipeline for one action."""

    decision: str  # ALLOW | DENY
    agent_uri: str
    capability: str
    checks: list = field(default_factory=list)
    reason: Optional[str] = None
    escalate: bool = False
    morpheus_called: bool = False
    vm_id: Optional[str] = None
    evidence_uri: Optional[str] = None
    chain_uri: Optional[str] = None
