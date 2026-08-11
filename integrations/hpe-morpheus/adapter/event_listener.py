"""Event listener — Morpheus webhooks/events into the provenance chain.

Morpheus emits asynchronous events (provisioned, configured, deleted). The
listener content-hashes and appends each event to the governing chain so that
infrastructure events that happen outside a direct request remain auditable.
"""

from __future__ import annotations

from typing import Optional

from crypto import SIG_ALG, canonical_json, sign
from provenance.morpheus_provenance_chain import (
    ChainLinkError,
    ProvenanceChain,
    ProvenanceEntry,
)


class EventListener:
    def __init__(self, node_public_key_hex: str) -> None:
        self.node_public_key_hex = node_public_key_hex
        self._handlers = []

    def on_event(self, handler) -> None:
        """Register a callback invoked with each recorded event."""
        self._handlers.append(handler)

    def record(
        self,
        chain: ProvenanceChain,
        action: str,
        object_uri: str,
        detail: dict,
        signer_private_key_hex: Optional[str],
    ) -> ProvenanceEntry:
        """Append a signed event entry to ``chain`` (chained to last entry)."""
        prev_hash = chain.entries[-1].hash() if chain.entries else None
        entry = ProvenanceEntry(
            seq=len(chain.entries) + 1,
            action=action,
            agent_uri="event://morpheus",
            object_uri=object_uri,
            decision="EVENT",
            detail=detail,
            prev_hash=prev_hash,
        )
        if signer_private_key_hex is not None:
            entry.sign(signer_private_key_hex)
        try:
            chain.append(entry)
        except ChainLinkError:
            raise
        for handler in self._handlers:
            handler(entry)
        return entry
