"""
Tests for SovereignStack Sync Engine

Validates the sync protocol from RFC 0004:
  - State digest comparison
  - SYNC_REQUEST / SYNC_ACK / EVENTS / SYNC_COMPLETE message flow
  - Missing range computation
  - Jurisdiction gating
  - Replay protection via monotonic sequences
"""

import time
import os
import tempfile
import pytest
from services.event_log import Event, EventLog, EventSigner
from services.sync_engine import SyncEngine, SyncMessage, MessageType


@pytest.fixture
def tmp_dirs():
    """Create temporary data directories for two nodes."""
    import shutil
    dirs = []
    for i in range(2):
        d = tempfile.mkdtemp(prefix=f"sovereign-sync-test-{i}-")
        dirs.append(d)
    yield dirs
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def signer():
    return EventSigner(hmac_secret="test-secret-key")


@pytest.fixture
def node_a(tmp_dirs, signer):
    """Create Node A with its own event log and sync engine."""
    event_log = EventLog(
        node_id="node-a",
        data_dir=os.path.join(tmp_dirs[0], "events"),
        signer=signer,
        jurisdiction="GLOBAL",
    )
    engine = SyncEngine(
        node_id="node-a",
        event_log=event_log,
        jurisdiction="GLOBAL",
    )
    return engine


@pytest.fixture
def node_b(tmp_dirs, signer):
    """Create Node B with its own event log and sync engine."""
    event_log = EventLog(
        node_id="node-b",
        data_dir=os.path.join(tmp_dirs[1], "events"),
        signer=signer,
        jurisdiction="GLOBAL",
    )
    engine = SyncEngine(
        node_id="node-b",
        event_log=event_log,
        jurisdiction="GLOBAL",
    )
    return engine


# ===========================================================================
# Event Log Tests
# ===========================================================================

class TestEventLog:

    def test_emit_creates_event(self, tmp_dirs, signer):
        log = EventLog("node-x", os.path.join(tmp_dirs[0], "events"), signer)
        event = log.emit("memory.vector.upsert", {"doc_id": "doc-1"})
        assert event.event_type == "memory.vector.upsert"
        assert event.node_id == "node-x"
        assert event.sequence == 1

    def test_monotonic_sequence(self, tmp_dirs, signer):
        log = EventLog("node-x", os.path.join(tmp_dirs[0], "events"), signer)
        e1 = log.emit("test.event", {"v": 1})
        e2 = log.emit("test.event", {"v": 2})
        e3 = log.emit("test.event", {"v": 3})
        assert e1.sequence == 1
        assert e2.sequence == 2
        assert e3.sequence == 3

    def test_event_signing(self, tmp_dirs, signer):
        log = EventLog("node-x", os.path.join(tmp_dirs[0], "events"), signer)
        event = log.emit("test.event", {"v": 1})
        assert event.signature is not None
        assert signer.verify(event)

    def test_ingest_remote_deduplication(self, tmp_dirs, signer):
        log = EventLog("node-x", os.path.join(tmp_dirs[0], "events"), signer)
        event = log.emit("test.event", {"v": 1})
        result = log.ingest_remote(event)
        assert result is False  # duplicate

    def test_ingest_remote_new_event(self, tmp_dirs, signer):
        log_a = EventLog("node-a", os.path.join(tmp_dirs[0], "events"), signer)
        log_b = EventLog("node-b", os.path.join(tmp_dirs[1], "events"), signer)

        event = log_a.emit("test.event", {"from": "a"})
        result = log_b.ingest_remote(event)
        assert result is True
        assert log_b.event_count == 1

    def test_digest_changes(self, tmp_dirs, signer):
        log = EventLog("node-x", os.path.join(tmp_dirs[0], "events"), signer)
        d1 = log.digest()
        log.emit("test.event", {"v": 1})
        d2 = log.digest()
        assert d1 != d2

    def test_persistence(self, tmp_dirs, signer):
        events_dir = os.path.join(tmp_dirs[0], "events")
        log1 = EventLog("node-x", events_dir, signer)
        log1.emit("test.event", {"v": 1})
        log1.emit("test.event", {"v": 2})

        # Create a new EventLog pointing to same dir
        log2 = EventLog("node-x", events_dir, signer)
        assert log2.event_count == 2
        assert log2.local_sequence == 2

    def test_query_by_type(self, tmp_dirs, signer):
        log = EventLog("node-x", os.path.join(tmp_dirs[0], "events"), signer)
        log.emit("memory.vector.upsert", {"doc_id": "d1"})
        log.emit("cache.set", {"session_id": "s1"})
        log.emit("memory.vector.upsert", {"doc_id": "d2"})

        memory_events = log.get_events(event_type="memory.vector.upsert")
        assert len(memory_events) == 2

    def test_jurisdiction_gating(self, tmp_dirs, signer):
        from services.event_log import JurisdictionPolicy
        policies = {
            "EU-GDPR": JurisdictionPolicy(
                allowed_egress=["EU-GDPR"],
                denied_types=["audit.log"],
            ),
        }
        log = EventLog(
            "node-x",
            os.path.join(tmp_dirs[0], "events"),
            signer,
            jurisdiction="EU-GDPR",
            jurisdiction_policies=policies,
        )
        log.emit("memory.vector.upsert", {"doc_id": "d1"})
        log.emit("audit.log", {"action": "test"})

        # Should filter out audit.log for EU-GDPR target
        events = log.get_events_for_sync("EU-GDPR")
        types = [e.event_type for e in events]
        assert "audit.log" not in types
        assert "memory.vector.upsert" in types

        # Should block all events for non-EU jurisdiction
        events = log.get_events_for_sync("US-HIPAA")
        assert len(events) == 0


# ===========================================================================
# Sync Engine Tests
# ===========================================================================

class TestSyncEngine:

    def test_initiate_sync(self, node_a, node_b):
        node_a.add_peer("node-b", "http://localhost:8084")
        request = node_a.initiate_sync("node-b")
        assert request is not None
        assert request.message_type == MessageType.SYNC_REQUEST
        assert request.node_id == "node-a"

    def test_already_in_sync(self, node_a, node_b):
        """Two empty nodes should report SYNC_COMPLETE immediately."""
        request = SyncMessage(
            message_type=MessageType.SYNC_REQUEST,
            node_id="node-a",
            session_id="test-session",
            state_digest=node_a.event_log.digest(),
            jurisdiction="GLOBAL",
        )
        response = node_b.handle_sync_request(request)
        assert response.message_type == MessageType.SYNC_COMPLETE

    def test_sync_request_triggers_ack_when_different(self, node_a, node_b):
        """When digests differ, responder sends SYNC_ACK."""
        # Add event to node_a only
        node_a.event_log.emit("test.event", {"from": "a"})

        request = SyncMessage(
            message_type=MessageType.SYNC_REQUEST,
            node_id="node-a",
            session_id="test-session",
            state_digest=node_a.event_log.digest(),
            jurisdiction="GLOBAL",
        )
        response = node_b.handle_sync_request(request)
        assert response.message_type == MessageType.SYNC_ACK

    def test_full_sync_cycle(self, node_a, node_b):
        """Simulate a full sync cycle between two nodes."""
        # Node A has events, Node B doesn't
        node_a.event_log.emit("memory.vector.upsert", {"doc_id": "d1"})
        node_a.event_log.emit("memory.vector.upsert", {"doc_id": "d2"})

        # Step 1: A sends SYNC_REQUEST
        request = node_a.initiate_sync.__wrapped__(node_a, "fake-peer") if hasattr(node_a.initiate_sync, '__wrapped__') else None
        # Manually create request since we don't have the peer registered
        request = SyncMessage(
            message_type=MessageType.SYNC_REQUEST,
            node_id="node-a",
            session_id="sess-1",
            state_digest=node_a.event_log.digest(),
            jurisdiction="GLOBAL",
        )

        # Step 2: B responds with SYNC_ACK
        ack = node_b.handle_sync_request(request)
        assert ack.message_type == MessageType.SYNC_ACK

        # Step 3: A sends EVENTS based on ACK
        events_msg = node_a.handle_sync_ack(ack)
        assert events_msg.message_type == MessageType.EVENTS
        assert len(events_msg.events) == 2

        # Step 4: B ingests events and sends SYNC_COMPLETE
        complete = node_b.handle_events(events_msg)
        assert complete.message_type == MessageType.SYNC_COMPLETE
        assert node_b.event_log.event_count == 2

    def test_bidirectional_sync(self, node_a, node_b):
        """Both nodes have unique events — after sync both should converge."""
        node_a.event_log.emit("memory.vector.upsert", {"doc_id": "from-a"})
        node_b.event_log.emit("memory.vector.upsert", {"doc_id": "from-b"})

        # Sync A → B
        events_for_b = SyncMessage(
            message_type=MessageType.EVENTS,
            node_id="node-a",
            session_id="sess-1",
            events=[e.to_dict() for e in node_a.event_log.get_events()],
            jurisdiction="GLOBAL",
        )
        node_b.handle_events(events_for_b)

        # Sync B → A
        events_for_a = SyncMessage(
            message_type=MessageType.EVENTS,
            node_id="node-b",
            session_id="sess-2",
            events=[e.to_dict() for e in node_b.event_log.get_events()],
            jurisdiction="GLOBAL",
        )
        node_a.handle_events(events_for_a)

        assert node_a.event_log.event_count == 2
        assert node_b.event_log.event_count == 2
        assert node_a.event_log.digest() == node_b.event_log.digest()

    def test_replay_protection(self, node_a, node_b):
        """Ingesting the same events twice should be idempotent."""
        node_a.event_log.emit("test.event", {"v": 1})
        events = [e.to_dict() for e in node_a.event_log.get_events()]

        msg = SyncMessage(
            message_type=MessageType.EVENTS,
            node_id="node-a",
            session_id="sess-1",
            events=events,
        )

        node_b.handle_events(msg)
        assert node_b.event_log.event_count == 1

        # Send again
        node_b.handle_events(msg)
        assert node_b.event_log.event_count == 1  # No duplicates

    def test_status(self, node_a):
        status = node_a.status()
        assert status["node_id"] == "node-a"
        assert status["running"] is False
        assert status["local_event_count"] == 0

    def test_peer_health_tracking(self, node_a):
        node_a.add_peer("peer-1", "http://peer1:8084")
        peers = node_a.get_peers()
        assert len(peers) == 1
        assert peers[0].is_healthy is True

        # Simulate failures
        peers[0].record_failure()
        assert peers[0].sync_failures == 1
        assert peers[0].is_healthy is True

        for _ in range(4):
            peers[0].record_failure()
        assert peers[0].is_healthy is False
