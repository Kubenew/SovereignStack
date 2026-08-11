"""Evidence package generation for governed Morpheus operations.

An :class:`EvidencePackage` wraps a decision, its provenance chain, and metadata
into one self-describing, signed object that can be verified by a third party
without any access to HPE Morpheus.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from crypto import SIG_ALG, canonical_json, sign
from provenance.morpheus_provenance_chain import ProvenanceChain


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvidencePackage:
    """A signed, self-describing evidence package."""

    package_id: str
    generated_by: str
    conformance_profile: str
    target_object: str
    action: str
    agent_uri: str
    capability: str
    decision: str
    checks: list
    chain: dict
    generated_at: str = field(default_factory=_ts)
    metadata: dict = field(default_factory=dict)
    signature: Optional[str] = None
    sig_alg: str = SIG_ALG

    @classmethod
    def new(
        cls,
        generated_by: str,
        conformance_profile: str,
        target_object: str,
        action: str,
        agent_uri: str,
        capability: str,
        decision: str,
        checks: list,
        chain: ProvenanceChain,
        metadata: Optional[dict] = None,
    ) -> "EvidencePackage":
        return cls(
            package_id=f"evidence-{uuid.uuid4().hex[:12]}",
            generated_by=generated_by,
            conformance_profile=conformance_profile,
            target_object=target_object,
            action=action,
            agent_uri=agent_uri,
            capability=capability,
            decision=decision,
            checks=checks,
            chain=chain.to_dict(),
            metadata=metadata or {},
        )

    def canonical_bytes(self) -> bytes:
        """Canonical bytes of the signed package (excludes the signature field,
        so signing and verification see identical bytes)."""
        return canonical_json(
            {
                "package_id": self.package_id,
                "generated_by": self.generated_by,
                "generated_at": self.generated_at,
                "conformance_profile": self.conformance_profile,
                "target_object": self.target_object,
                "action": self.action,
                "agent_uri": self.agent_uri,
                "capability": self.capability,
                "decision": self.decision,
                "checks": self.checks,
                "chain": self.chain,
                "metadata": self.metadata,
            }
        )

    def sign(self, node_private_key_hex: str) -> "EvidencePackage":
        self.sig_alg = SIG_ALG
        self.signature = sign(self.canonical_bytes(), node_private_key_hex)
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EvidencePackage":
        known = {
            k: v
            for k, v in data.items()
            if k
            in {
                "package_id",
                "generated_by",
                "conformance_profile",
                "target_object",
                "action",
                "agent_uri",
                "capability",
                "decision",
                "checks",
                "chain",
                "generated_at",
                "metadata",
                "signature",
                "sig_alg",
            }
        }
        return cls(**known)

    def save(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "EvidencePackage":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
