"""Morpheus provenance chain — tamper-evident audit trail.

Every governed action produces a :class:`ProvenanceEntry` with a content hash
and an Ed25519 signature over its canonical form. Entries are linked by
``prev_hash`` into a Merkle-style chain, so any modification is detected at the
exact entry it occurred.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from crypto import canonical_json, hash_bytes, sign, verify


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProvenanceEntry:
    """A single signed, content-hashed record in a provenance chain."""

    seq: int
    action: str
    agent_uri: str
    object_uri: str
    decision: str
    detail: dict
    ts: str = field(default_factory=_ts)
    nonce: str = field(default_factory=lambda: uuid.uuid4().hex)
    prev_hash: Optional[str] = None
    content_hash: str = ""
    signature: Optional[str] = None
    sig_alg: str = "ed25519"

    def __post_init__(self) -> None:
        if not self.content_hash:
            self.content_hash = hash_bytes(self._content_bytes())

    def _content_bytes(self) -> bytes:
        """Canonical bytes of the semantic content (tamper-evident payload)."""
        return canonical_json(
            {
                "action": self.action,
                "agent_uri": self.agent_uri,
                "object_uri": self.object_uri,
                "decision": self.decision,
                "detail": self.detail,
                "ts": self.ts,
                "nonce": self.nonce,
            }
        )

    def canonical_bytes(self) -> bytes:
        """Canonical bytes of the full entry, including linkage and signature."""
        return canonical_json(
            {
                "seq": self.seq,
                "content_hash": self.content_hash,
                "prev_hash": self.prev_hash,
                "signature": self.signature,
                "sig_alg": self.sig_alg,
                **{
                    "action": self.action,
                    "agent_uri": self.agent_uri,
                    "object_uri": self.object_uri,
                    "decision": self.decision,
                    "detail": self.detail,
                    "ts": self.ts,
                    "nonce": self.nonce,
                },
            }
        )

    def signature_payload_bytes(self) -> bytes:
        """Canonical bytes that are actually signed.

        The signature field itself is excluded so signing and verification see
        identical bytes, while linkage hashes (``hash()``) still cover the
        signature via ``canonical_bytes``.
        """
        return canonical_json(
            {
                "seq": self.seq,
                "content_hash": self.content_hash,
                "prev_hash": self.prev_hash,
                "sig_alg": self.sig_alg,
                "action": self.action,
                "agent_uri": self.agent_uri,
                "object_uri": self.object_uri,
                "decision": self.decision,
                "detail": self.detail,
                "ts": self.ts,
                "nonce": self.nonce,
            }
        )

    def hash(self) -> str:
        return hash_bytes(self.canonical_bytes())

    def sign(self, private_key_hex: str) -> "ProvenanceEntry":
        from crypto import SIG_ALG

        self.sig_alg = SIG_ALG
        self.signature = sign(self.signature_payload_bytes(), private_key_hex)
        return self


@dataclass
class ProvenanceChain:
    """An append-only chain enforcing hash linkage between entries."""

    target: str
    entries: list = field(default_factory=list)

    def append(self, entry: ProvenanceEntry, private_key_hex: Optional[str] = None) -> ProvenanceEntry:
        expected_prev = self.entries[-1].hash() if self.entries else None
        if entry.prev_hash != expected_prev:
            raise ChainLinkError(
                f"linkage broken: expected prev_hash={expected_prev}, "
                f"found {entry.prev_hash}"
            )
        if private_key_hex is not None:
            entry.sign(private_key_hex)
        self.entries.append(entry)
        return entry

    def verify(
        self,
        public_keys: Callable[[str], Optional[str]],
        node_public_key: Optional[str] = None,
    ) -> tuple[bool, list[str]]:
        """Verify linkage, content hashes, and signatures.

        ``public_keys`` maps an agent URI to its public key hex; entries signed
        by the governing node are verified against ``node_public_key``.
        """
        reasons: list[str] = []
        expected_prev: Optional[str] = None
        for entry in self.entries:
            if entry.prev_hash != expected_prev:
                reasons.append(f"entry {entry.seq}: broken linkage")
                return False, reasons
            if entry.content_hash != hash_bytes(entry._content_bytes()):
                reasons.append(f"entry {entry.seq}: content tampered")
                return False, reasons
            if entry.signature:
                keys: list[str] = []
                agent_key = public_keys(entry.agent_uri)
                if agent_key:
                    keys.append(agent_key)
                if node_public_key and node_public_key not in keys:
                    keys.append(node_public_key)
                if not keys:
                    reasons.append(f"entry {entry.seq}: unknown public key")
                    return False, reasons
                if not any(
                    verify(entry.signature_payload_bytes(), entry.signature, k)
                    for k in keys
                ):
                    reasons.append(f"entry {entry.seq}: invalid signature")
                    return False, reasons
            else:
                reasons.append(f"entry {entry.seq}: unsigned entry")
                return False, reasons
            expected_prev = entry.hash()
        if not self.entries:
            reasons.append("empty chain")
            return False, reasons
        reasons.append(f"chain verified: {len(self.entries)} entries")
        return True, reasons

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "entries": [asdict(e) for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProvenanceChain":
        chain = cls(target=data["target"])
        chain.entries = [ProvenanceEntry(**e) for e in data["entries"]]
        return chain


class ChainLinkError(Exception):
    """Raised when an append violates hash linkage."""


def resolve_key_from(registry: dict) -> Callable[[str], Optional[str]]:
    """Build a resolver over a plain ``{agent_uri: public_key_hex}`` dict."""

    def _resolve(agent_uri: str) -> Optional[str]:
        return registry.get(agent_uri)

    return _resolve
