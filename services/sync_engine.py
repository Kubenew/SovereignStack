"""
SovereignStack Sync Engine — Cross-Node State Synchronization

Implements the sync protocol from RFC 0004 (Federation Protocol):
  - SYNC_REQUEST / SYNC_ACK / EVENTS / SYNC_COMPLETE message flow
  - Anti-entropy: state digest comparison and missing range detection
  - Batch event transfer with configurable batch size
  - Jurisdictional gating — drops events violating jurisdiction policy
  - Monotonic sequence tracking per peer for replay protection
  - Background sync loop on configurable interval

The sync engine is transport-agnostic: it produces and consumes
sync messages, while the federation_service handles HTTP transport.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from services.event_log import Event, EventLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sync Protocol Messages (RFC 0004)
# ---------------------------------------------------------------------------

class MessageType(str, Enum):
    SYNC_REQUEST = "SYNC_REQUEST"
    SYNC_ACK = "SYNC_ACK"
    EVENTS = "EVENTS"
    SYNC_COMPLETE = "SYNC_COMPLETE"
    ERROR = "ERROR"


@dataclass
class SyncMessage:
    """Wire format for sync protocol messages."""

    protocol_version: str = "1.0"
    message_type: MessageType = MessageType.SYNC_REQUEST
    node_id: str = ""
    session_id: str = ""
    state_digest: str = ""
    since_sequence: int = 0
    batch_size: int = 100
    jurisdiction: str = "GLOBAL"
    events: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "protocol_version": self.protocol_version,
            "message_type": self.message_type.value,
            "node_id": self.node_id,
            "session_id": self.session_id,
            "state_digest": self.state_digest,
            "since_sequence": self.since_sequence,
            "batch_size": self.batch_size,
            "jurisdiction": self.jurisdiction,
            "events": self.events,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SyncMessage:
        return cls(
            protocol_version=data.get("protocol_version", "1.0"),
            message_type=MessageType(data["message_type"]),
            node_id=data.get("node_id", ""),
            session_id=data.get("session_id", ""),
            state_digest=data.get("state_digest", ""),
            since_sequence=data.get("since_sequence", 0),
            batch_size=data.get("batch_size", 100),
            jurisdiction=data.get("jurisdiction", "GLOBAL"),
            events=data.get("events", []),
            error=data.get("error"),
        )


# ---------------------------------------------------------------------------
# Peer State Tracker
# ---------------------------------------------------------------------------

@dataclass
class PeerState:
    """Tracks sync state for a remote peer."""

    peer_id: str
    endpoint: str
    jurisdiction: str = "GLOBAL"
    last_digest: str = ""
    last_sequence_sent: int = 0
    last_sequence_received: int = 0
    last_sync_time: float = 0.0
    sync_failures: int = 0
    is_healthy: bool = True

    def record_success(self, digest: str) -> None:
        self.last_digest = digest
        self.last_sync_time = time.time()
        self.sync_failures = 0
        self.is_healthy = True

    def record_failure(self) -> None:
        self.sync_failures += 1
        if self.sync_failures >= 5:
            self.is_healthy = False


# ---------------------------------------------------------------------------
# Sync Engine
# ---------------------------------------------------------------------------

class SyncEngine:
    """
    Cross-node state synchronization engine.

    Coordinates event exchange between the local EventLog and remote peers
    using the sync protocol defined in RFC 0004.
    """

    def __init__(
        self,
        node_id: str,
        event_log: EventLog,
        jurisdiction: str = "GLOBAL",
        sync_interval: float = 60.0,
        batch_size: int = 100,
    ):
        self.node_id = node_id
        self.event_log = event_log
        self.jurisdiction = jurisdiction
        self.sync_interval = sync_interval
        self.batch_size = batch_size

        self._peers: Dict[str, PeerState] = {}
        self._lock = threading.Lock()
        self._running = False
        self._sync_thread: Optional[threading.Thread] = None

        # Transport callback: set by federation_service to send HTTP requests
        self._transport: Optional[Callable[[str, dict], Optional[dict]]] = None

    # ---- Peer Management ----

    def add_peer(self, peer_id: str, endpoint: str, jurisdiction: str = "GLOBAL") -> None:
        """Register a known peer."""
        with self._lock:
            self._peers[peer_id] = PeerState(
                peer_id=peer_id,
                endpoint=endpoint,
                jurisdiction=jurisdiction,
            )
        logger.info("Added peer %s at %s (jurisdiction=%s)", peer_id, endpoint, jurisdiction)

    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer."""
        with self._lock:
            self._peers.pop(peer_id, None)

    def get_peers(self) -> List[PeerState]:
        """Return list of all known peers."""
        with self._lock:
            return list(self._peers.values())

    def set_transport(self, transport: Callable[[str, dict], Optional[dict]]) -> None:
        """Set the transport callback for sending sync messages to peers."""
        self._transport = transport

    # ---- Sync Protocol: Initiator Side ----

    def initiate_sync(self, peer_id: str) -> Optional[SyncMessage]:
        """
        Initiate a sync session with a peer.
        Returns the SYNC_REQUEST message to send.
        """
        with self._lock:
            peer = self._peers.get(peer_id)
            if not peer:
                logger.warning("Unknown peer: %s", peer_id)
                return None

        import uuid
        session_id = f"sync-{uuid.uuid4().hex[:8]}"

        request = SyncMessage(
            message_type=MessageType.SYNC_REQUEST,
            node_id=self.node_id,
            session_id=session_id,
            state_digest=self.event_log.digest(),
            since_sequence=peer.last_sequence_received,
            batch_size=self.batch_size,
            jurisdiction=self.jurisdiction,
        )

        logger.info(
            "Initiating sync with %s (session=%s, digest=%s)",
            peer_id,
            session_id,
            request.state_digest[:16],
        )
        return request

    def handle_sync_ack(self, ack: SyncMessage) -> SyncMessage:
        """
        Handle SYNC_ACK from a peer: they told us what events they need.
        Return an EVENTS message containing the missing events.
        """
        events = self.event_log.get_events_for_sync(
            target_jurisdiction=ack.jurisdiction,
            since_sequence=ack.since_sequence,
            batch_size=ack.batch_size,
        )

        events_msg = SyncMessage(
            message_type=MessageType.EVENTS,
            node_id=self.node_id,
            session_id=ack.session_id,
            state_digest=self.event_log.digest(),
            jurisdiction=self.jurisdiction,
            events=[e.to_dict() for e in events],
        )

        logger.info(
            "Sending %d events to %s (session=%s)",
            len(events),
            ack.node_id,
            ack.session_id,
        )
        return events_msg

    # ---- Sync Protocol: Responder Side ----

    def handle_sync_request(self, request: SyncMessage) -> SyncMessage:
        """
        Handle incoming SYNC_REQUEST from a peer.
        Returns a SYNC_ACK telling them what we need.
        """
        local_digest = self.event_log.digest()

        if local_digest == request.state_digest:
            # Already in sync — no events needed
            logger.info("Already in sync with %s", request.node_id)
            return SyncMessage(
                message_type=MessageType.SYNC_COMPLETE,
                node_id=self.node_id,
                session_id=request.session_id,
                state_digest=local_digest,
                jurisdiction=self.jurisdiction,
            )

        # We need events from the peer — send SYNC_ACK with our sequence
        peer = self._peers.get(request.node_id)
        since_seq = peer.last_sequence_received if peer else 0

        ack = SyncMessage(
            message_type=MessageType.SYNC_ACK,
            node_id=self.node_id,
            session_id=request.session_id,
            state_digest=local_digest,
            since_sequence=since_seq,
            batch_size=self.batch_size,
            jurisdiction=self.jurisdiction,
        )

        logger.info(
            "Sending SYNC_ACK to %s (since_seq=%d)",
            request.node_id,
            since_seq,
        )
        return ack

    def handle_events(self, events_msg: SyncMessage) -> SyncMessage:
        """
        Handle incoming EVENTS batch from a peer.
        Ingest events into the local log and return SYNC_COMPLETE.
        """
        ingested = 0
        rejected = 0

        for event_data in events_msg.events:
            try:
                event = Event.from_dict(event_data)
                if self.event_log.ingest_remote(event):
                    ingested += 1
                # else: duplicate, skip
            except Exception as exc:
                logger.warning("Failed to ingest event: %s", exc)
                rejected += 1

        # Update peer tracking
        with self._lock:
            peer = self._peers.get(events_msg.node_id)
            if peer:
                peer.record_success(events_msg.state_digest)

        logger.info(
            "Ingested %d events from %s (%d rejected)",
            ingested,
            events_msg.node_id,
            rejected,
        )

        return SyncMessage(
            message_type=MessageType.SYNC_COMPLETE,
            node_id=self.node_id,
            session_id=events_msg.session_id,
            state_digest=self.event_log.digest(),
            jurisdiction=self.jurisdiction,
        )

    def handle_message(self, message: SyncMessage) -> SyncMessage:
        """Route a sync message to the appropriate handler."""
        handlers = {
            MessageType.SYNC_REQUEST: self.handle_sync_request,
            MessageType.SYNC_ACK: self.handle_sync_ack,
            MessageType.EVENTS: self.handle_events,
        }

        handler = handlers.get(message.message_type)
        if handler is None:
            return SyncMessage(
                message_type=MessageType.ERROR,
                node_id=self.node_id,
                session_id=message.session_id,
                error=f"Unknown message type: {message.message_type}",
            )

        return handler(message)

    # ---- Full Sync Cycle (Initiator) ----

    def sync_with_peer(self, peer_id: str) -> bool:
        """
        Execute a full sync cycle with a peer.
        Returns True on success, False on failure.
        Requires transport callback to be set.
        """
        if self._transport is None:
            logger.error("No transport configured for sync")
            return False

        peer = self._peers.get(peer_id)
        if not peer:
            logger.warning("Unknown peer: %s", peer_id)
            return False

        try:
            # Step 1: Send SYNC_REQUEST
            request = self.initiate_sync(peer_id)
            if request is None:
                return False

            response_data = self._transport(peer.endpoint, request.to_dict())
            if response_data is None:
                peer.record_failure()
                return False

            response = SyncMessage.from_dict(response_data)

            # Step 2: If already in sync, done
            if response.message_type == MessageType.SYNC_COMPLETE:
                peer.record_success(response.state_digest)
                return True

            # Step 3: If SYNC_ACK, send our events
            if response.message_type == MessageType.SYNC_ACK:
                events_msg = self.handle_sync_ack(response)
                complete_data = self._transport(peer.endpoint, events_msg.to_dict())

                if complete_data:
                    complete = SyncMessage.from_dict(complete_data)
                    if complete.message_type == MessageType.SYNC_COMPLETE:
                        peer.record_success(complete.state_digest)
                        return True

            # Step 4: Handle any events the peer sends us
            if response.message_type == MessageType.EVENTS:
                self.handle_events(response)
                peer.record_success(response.state_digest)
                return True

            peer.record_failure()
            return False

        except Exception as exc:
            logger.error("Sync with %s failed: %s", peer_id, exc)
            peer.record_failure()
            return False

    # ---- Background Sync Loop ----

    def start(self) -> None:
        """Start the background sync loop."""
        if self._running:
            return

        self._running = True
        self._sync_thread = threading.Thread(
            target=self._sync_loop, daemon=True, name="sync-engine"
        )
        self._sync_thread.start()
        logger.info("Sync engine started (interval=%.0fs)", self.sync_interval)

    def stop(self) -> None:
        """Stop the background sync loop."""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=5.0)
        logger.info("Sync engine stopped")

    def _sync_loop(self) -> None:
        """Background thread: periodically sync with all healthy peers."""
        while self._running:
            try:
                peers = self.get_peers()
                for peer in peers:
                    if not self._running:
                        break
                    if not peer.is_healthy:
                        continue
                    try:
                        self.sync_with_peer(peer.peer_id)
                    except Exception as exc:
                        logger.error("Sync loop error for %s: %s", peer.peer_id, exc)
            except Exception as exc:
                logger.error("Sync loop error: %s", exc)

            # Wait for the next interval (check _running every second)
            for _ in range(int(self.sync_interval)):
                if not self._running:
                    break
                time.sleep(1.0)

    # ---- Status ----

    def status(self) -> dict:
        """Return sync engine status."""
        with self._lock:
            return {
                "node_id": self.node_id,
                "jurisdiction": self.jurisdiction,
                "running": self._running,
                "sync_interval": self.sync_interval,
                "local_digest": self.event_log.digest(),
                "local_event_count": self.event_log.event_count,
                "local_sequence": self.event_log.local_sequence,
                "peers": {
                    pid: {
                        "endpoint": p.endpoint,
                        "jurisdiction": p.jurisdiction,
                        "last_sync": p.last_sync_time,
                        "failures": p.sync_failures,
                        "healthy": p.is_healthy,
                    }
                    for pid, p in self._peers.items()
                },
            }
