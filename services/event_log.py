"""
SovereignStack Event Log — Event Sourcing Engine

Implements the event log subsystem from RFC 0006 (Memory Specification):
  - Persistent append-only storage (JSON lines file)
  - State digest computation (SHA-256) for anti-entropy sync
  - Event filtering by type, time range, sequence, and jurisdiction
  - Ed25519 event signing and verification
  - Monotonic sequence numbers per node for replay protection

Events are the source of truth for cross-node CRDT synchronization.
Vector indices and KV caches are reconstructed by replaying events.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event Schema
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """
    A single event in the append-only log.

    Matches RFC 0004 event format:
      {event_id, type, node_id, timestamp, data, signature, jurisdiction, sequence}
    """

    event_id: str
    event_type: str  # e.g., "memory.vector.upsert", "cache.set"
    node_id: str
    timestamp: float
    sequence: int  # monotonic per node
    data: Dict[str, Any]
    jurisdiction: str = "GLOBAL"
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "data": self.data,
            "jurisdiction": self.jurisdiction,
            "signature": self.signature,
        }

    def signing_payload(self) -> bytes:
        """Canonical byte representation for signing (excludes signature field)."""
        canonical = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "data": self.data,
            "jurisdiction": self.jurisdiction,
        }
        return json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> Event:
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            sequence=data["sequence"],
            data=data["data"],
            jurisdiction=data.get("jurisdiction", "GLOBAL"),
            signature=data.get("signature"),
        )


# ---------------------------------------------------------------------------
# Event Signer — Ed25519 signing and verification
# ---------------------------------------------------------------------------

class EventSigner:
    """
    Ed25519 event signing and verification.

    Falls back to HMAC-SHA256 if Ed25519 keys are not available
    (e.g., in development/test environments).
    """

    def __init__(self, private_key_path: Optional[str] = None, hmac_secret: Optional[str] = None):
        self._private_key = None
        self._public_key = None
        self._hmac_secret = hmac_secret or os.getenv("EVENT_SIGNING_SECRET", "sovereign-dev-secret")

        if private_key_path and os.path.exists(private_key_path):
            try:
                # Attempt Ed25519 signing via cryptography library
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
                from cryptography.hazmat.primitives.serialization import load_pem_private_key

                with open(private_key_path, "rb") as f:
                    self._private_key = load_pem_private_key(f.read(), password=None)
                self._public_key = self._private_key.public_key()
                logger.info("Event signing initialized with Ed25519 key")
            except (ImportError, Exception) as exc:
                logger.warning("Ed25519 unavailable (%s), falling back to HMAC-SHA256", exc)

    def sign(self, event: Event) -> str:
        """Sign an event, returning the signature as hex string."""
        payload = event.signing_payload()

        if self._private_key is not None:
            sig = self._private_key.sign(payload)
            return sig.hex()

        # HMAC-SHA256 fallback
        import hmac as _hmac
        return _hmac.new(
            self._hmac_secret.encode(), payload, hashlib.sha256
        ).hexdigest()

    def verify(self, event: Event) -> bool:
        """Verify an event's signature. Returns True if valid."""
        if event.signature is None:
            return False

        payload = event.signing_payload()

        if self._public_key is not None:
            try:
                self._public_key.verify(bytes.fromhex(event.signature), payload)
                return True
            except Exception:
                return False

        # HMAC-SHA256 fallback verification
        import hmac as _hmac
        expected = _hmac.new(
            self._hmac_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return _hmac.compare_digest(expected, event.signature)


# ---------------------------------------------------------------------------
# Jurisdiction Policy
# ---------------------------------------------------------------------------

@dataclass
class JurisdictionPolicy:
    """Jurisdiction gating rules from RFC 0004."""

    allowed_egress: List[str] = field(default_factory=lambda: ["GLOBAL"])
    denied_types: List[str] = field(default_factory=list)

    def allows_event(self, event: Event, target_jurisdiction: str) -> bool:
        """Check if an event is allowed to be sent to a target jurisdiction."""
        if target_jurisdiction not in self.allowed_egress:
            return False
        if event.event_type in self.denied_types:
            return False
        return True


DEFAULT_JURISDICTION_POLICIES: Dict[str, JurisdictionPolicy] = {
    "EU-GDPR": JurisdictionPolicy(
        allowed_egress=["EU-GDPR"],
        denied_types=["audit.log"],
    ),
    "US-HIPAA": JurisdictionPolicy(
        allowed_egress=["US-HIPAA"],
        denied_types=["audit.log", "memory.vector.upsert"],
    ),
    "GLOBAL": JurisdictionPolicy(
        allowed_egress=["EU-GDPR", "US-HIPAA", "GLOBAL"],
        denied_types=["audit.log"],
    ),
}


# ---------------------------------------------------------------------------
# EventLog — Persistent append-only event store
# ---------------------------------------------------------------------------

class EventLog:
    """
    Persistent, append-only event log with sequence tracking.

    Storage: JSON lines file at `{data_dir}/events.jsonl`
    Thread-safe for concurrent append operations.
    """

    def __init__(
        self,
        node_id: str,
        data_dir: str = "/app/data/events",
        signer: Optional[EventSigner] = None,
        jurisdiction: str = "GLOBAL",
        jurisdiction_policies: Optional[Dict[str, JurisdictionPolicy]] = None,
    ):
        self.node_id = node_id
        self.data_dir = data_dir
        self.jurisdiction = jurisdiction
        self.signer = signer or EventSigner()
        self.jurisdiction_policies = jurisdiction_policies or DEFAULT_JURISDICTION_POLICIES

        self._lock = threading.Lock()
        self._sequence = 0
        self._events: Dict[str, Event] = {}
        self._subscribers: List[Callable[[Event], None]] = []

        os.makedirs(data_dir, exist_ok=True)
        self._log_path = os.path.join(data_dir, "events.jsonl")
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing events from disk on startup."""
        if not os.path.exists(self._log_path):
            return

        max_seq = 0
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    event = Event.from_dict(data)
                    self._events[event.event_id] = event
                    if event.node_id == self.node_id:
                        max_seq = max(max_seq, event.sequence)
                except (json.JSONDecodeError, KeyError) as exc:
                    logger.warning("Skipping corrupt event line: %s", exc)

        self._sequence = max_seq
        logger.info(
            "Loaded %d events from disk (local sequence=%d)",
            len(self._events),
            self._sequence,
        )

    def emit(self, event_type: str, data: Dict[str, Any]) -> Event:
        """Create and persist a new event. Returns the Event."""
        with self._lock:
            self._sequence += 1
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                node_id=self.node_id,
                timestamp=time.time(),
                sequence=self._sequence,
                data=data,
                jurisdiction=self.jurisdiction,
            )

            # Sign the event
            event.signature = self.signer.sign(event)

            # Persist to disk
            self._events[event.event_id] = event
            self._append_to_disk(event)

        # Notify subscribers (outside lock)
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception as exc:
                logger.error("Event subscriber error: %s", exc)

        return event

    def ingest_remote(self, event: Event) -> bool:
        """
        Ingest an event received from a remote node.
        Returns True if the event was new, False if duplicate.
        """
        with self._lock:
            if event.event_id in self._events:
                return False

            # Verify signature
            if not self.signer.verify(event):
                logger.warning("Rejected event %s: invalid signature", event.event_id)
                return False

            self._events[event.event_id] = event
            self._append_to_disk(event)

        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception as exc:
                logger.error("Event subscriber error: %s", exc)

        return True

    def _append_to_disk(self, event: Event) -> None:
        """Append a single event to the JSON lines file."""
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), separators=(",", ":")) + "\n")
        except OSError as exc:
            logger.error("Failed to persist event %s: %s", event.event_id, exc)

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        """Register a callback for new events."""
        self._subscribers.append(callback)

    # ---- Query methods ----

    def get_events(
        self,
        since_sequence: int = 0,
        event_type: Optional[str] = None,
        node_id: Optional[str] = None,
        since_timestamp: Optional[float] = None,
        until_timestamp: Optional[float] = None,
        limit: int = 1000,
    ) -> List[Event]:
        """Query events with optional filters."""
        events = sorted(self._events.values(), key=lambda e: (e.timestamp, e.sequence))

        result = []
        for event in events:
            if event.node_id == self.node_id and event.sequence <= since_sequence:
                continue
            if event_type and event.event_type != event_type:
                continue
            if node_id and event.node_id != node_id:
                continue
            if since_timestamp and event.timestamp < since_timestamp:
                continue
            if until_timestamp and event.timestamp > until_timestamp:
                continue
            result.append(event)
            if len(result) >= limit:
                break

        return result

    def get_events_for_sync(
        self,
        target_jurisdiction: str,
        since_sequence: int = 0,
        batch_size: int = 100,
    ) -> List[Event]:
        """
        Get events suitable for sending to a peer in target_jurisdiction.
        Applies jurisdiction gating per RFC 0004.
        """
        policy = self.jurisdiction_policies.get(
            self.jurisdiction,
            JurisdictionPolicy(),
        )

        events = self.get_events(since_sequence=since_sequence, limit=batch_size)
        return [e for e in events if policy.allows_event(e, target_jurisdiction)]

    def digest(self) -> str:
        """Compute SHA-256 state digest for anti-entropy comparison."""
        event_ids = sorted(self._events.keys())
        content = json.dumps(event_ids, separators=(",", ":"))
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    @property
    def local_sequence(self) -> int:
        """Current monotonic sequence number for this node."""
        return self._sequence

    @property
    def event_count(self) -> int:
        return len(self._events)

    def get_event(self, event_id: str) -> Optional[Event]:
        return self._events.get(event_id)
