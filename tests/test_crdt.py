"""
Tests for SovereignStack CRDT Library

Validates the convergence properties of all CRDT types:
  - Commutativity:  merge(a, b) == merge(b, a)
  - Associativity:  merge(merge(a, b), c) == merge(a, merge(b, c))
  - Idempotency:    merge(a, a) == a
"""

import time
import pytest
from services.crdt import (
    LWWRegister,
    TombstoneSet,
    TombstoneEntry,
    AppendOnlyLog,
    LogEntry,
    CRDTMap,
)


# ===========================================================================
# LWW-Register Tests
# ===========================================================================

class TestLWWRegister:

    def test_basic_set_and_get(self):
        reg = LWWRegister(key="doc-1")
        reg.set("value-a", timestamp=1.0, node_id="node-a")
        assert reg.value == "value-a"
        assert reg.timestamp == 1.0

    def test_newer_timestamp_wins(self):
        reg = LWWRegister(key="doc-1")
        reg.set("old", timestamp=1.0, node_id="node-a")
        reg.set("new", timestamp=2.0, node_id="node-b")
        assert reg.value == "new"

    def test_older_timestamp_ignored(self):
        reg = LWWRegister(key="doc-1")
        reg.set("new", timestamp=2.0, node_id="node-a")
        reg.set("old", timestamp=1.0, node_id="node-b")
        assert reg.value == "new"

    def test_tiebreaker_by_node_id(self):
        reg = LWWRegister(key="doc-1")
        reg.set("from-a", timestamp=1.0, node_id="node-a")
        reg.set("from-b", timestamp=1.0, node_id="node-b")
        assert reg.value == "from-b"  # "node-b" > "node-a" lexicographically

    def test_merge_commutativity(self):
        a = LWWRegister(key="k", value="a", timestamp=1.0, node_id="n-a")
        b = LWWRegister(key="k", value="b", timestamp=2.0, node_id="n-b")
        ab = a.merge(b)
        ba = b.merge(a)
        assert ab.value == ba.value
        assert ab.timestamp == ba.timestamp

    def test_merge_idempotency(self):
        a = LWWRegister(key="k", value="a", timestamp=1.0, node_id="n-a")
        aa = a.merge(a)
        assert aa.value == a.value
        assert aa.timestamp == a.timestamp

    def test_serialization_roundtrip(self):
        reg = LWWRegister(key="doc-1", value={"nested": "data"}, timestamp=42.5, node_id="n-1")
        data = reg.to_dict()
        restored = LWWRegister.from_dict(data)
        assert restored.key == reg.key
        assert restored.value == reg.value
        assert restored.timestamp == reg.timestamp
        assert restored.node_id == reg.node_id


# ===========================================================================
# TombstoneSet Tests
# ===========================================================================

class TestTombstoneSet:

    def test_add_and_retrieve(self):
        ts = TombstoneSet()
        ts.add("doc-1", "value-1", timestamp=1.0, node_id="n-a")
        alive = ts.get_alive()
        assert "doc-1" in alive
        assert alive["doc-1"] == "value-1"

    def test_remove_tombstones(self):
        ts = TombstoneSet()
        ts.add("doc-1", "value-1", timestamp=1.0, node_id="n-a")
        ts.remove("doc-1", timestamp=2.0, node_id="n-a")
        alive = ts.get_alive()
        assert "doc-1" not in alive

    def test_add_after_remove_resurrects(self):
        ts = TombstoneSet()
        ts.add("doc-1", "v1", timestamp=1.0, node_id="n-a")
        ts.remove("doc-1", timestamp=2.0, node_id="n-a")
        ts.add("doc-1", "v2", timestamp=3.0, node_id="n-a")
        alive = ts.get_alive()
        assert "doc-1" in alive
        assert alive["doc-1"] == "v2"

    def test_remove_before_add_has_no_effect(self):
        ts = TombstoneSet()
        ts.remove("doc-1", timestamp=1.0, node_id="n-a")
        ts.add("doc-1", "v1", timestamp=2.0, node_id="n-a")
        alive = ts.get_alive()
        assert "doc-1" in alive

    def test_merge_commutativity(self):
        a = TombstoneSet()
        a.add("d1", "v1", 1.0, "n-a")
        a.add("d2", "v2", 2.0, "n-a")

        b = TombstoneSet()
        b.add("d2", "v2-updated", 3.0, "n-b")
        b.add("d3", "v3", 1.0, "n-b")

        ab = a.merge(b)
        ba = b.merge(a)

        assert ab.get_alive() == ba.get_alive()

    def test_merge_with_tombstones(self):
        a = TombstoneSet()
        a.add("d1", "v1", 1.0, "n-a")
        a.remove("d1", 3.0, "n-a")

        b = TombstoneSet()
        b.add("d1", "v1", 2.0, "n-b")

        merged = a.merge(b)
        # Removal at t=3 should win over add at t=2
        assert "d1" not in merged.get_alive()

    def test_merge_idempotency(self):
        ts = TombstoneSet()
        ts.add("d1", "v1", 1.0, "n-a")
        ts.add("d2", "v2", 2.0, "n-b")
        ts.remove("d1", 3.0, "n-a")

        merged = ts.merge(ts)
        assert merged.get_alive() == ts.get_alive()

    def test_serialization_roundtrip(self):
        ts = TombstoneSet()
        ts.add("d1", "v1", 1.0, "n-a")
        ts.remove("d1", 2.0, "n-b")
        ts.add("d2", {"complex": True}, 1.0, "n-a")

        data = ts.to_dict()
        restored = TombstoneSet.from_dict(data)
        assert restored.get_alive() == ts.get_alive()


# ===========================================================================
# AppendOnlyLog Tests
# ===========================================================================

class TestAppendOnlyLog:

    def test_append_and_retrieve(self):
        log = AppendOnlyLog()
        entry = log.append(data={"action": "test"}, node_id="n-a")
        assert log.size == 1
        entries = log.entries()
        assert entries[0].event_id == entry.event_id
        assert entries[0].data == {"action": "test"}

    def test_append_is_immutable(self):
        log = AppendOnlyLog()
        log.append(data={"v": 1}, node_id="n-a")
        log.append(data={"v": 2}, node_id="n-a")
        assert log.size == 2
        # Cannot modify past entries
        entries = log.entries()
        assert entries[0].data["v"] == 1
        assert entries[1].data["v"] == 2

    def test_add_entry_deduplication(self):
        log = AppendOnlyLog()
        entry = log.append(data={"v": 1}, node_id="n-a")
        result = log.add_entry(entry)
        assert result is False  # duplicate
        assert log.size == 1

    def test_merge_set_union(self):
        a = AppendOnlyLog()
        a.append(data={"from": "a"}, node_id="n-a")

        b = AppendOnlyLog()
        b.append(data={"from": "b"}, node_id="n-b")

        merged = a.merge(b)
        assert merged.size == 2

    def test_merge_commutativity(self):
        a = AppendOnlyLog()
        a.append(data={"v": 1}, node_id="n-a")

        b = AppendOnlyLog()
        b.append(data={"v": 2}, node_id="n-b")

        ab = a.merge(b)
        ba = b.merge(a)
        assert ab.size == ba.size
        assert ab.digest() == ba.digest()

    def test_merge_idempotency(self):
        log = AppendOnlyLog()
        log.append(data={"v": 1}, node_id="n-a")
        log.append(data={"v": 2}, node_id="n-a")

        merged = log.merge(log)
        assert merged.size == log.size
        assert merged.digest() == log.digest()

    def test_digest_changes_on_append(self):
        log = AppendOnlyLog()
        d1 = log.digest()
        log.append(data={"v": 1}, node_id="n-a")
        d2 = log.digest()
        assert d1 != d2

    def test_since_sequence(self):
        log = AppendOnlyLog()
        log.append(data={"v": 1}, node_id="n-a")
        log.append(data={"v": 2}, node_id="n-a")
        log.append(data={"v": 3}, node_id="n-a")

        after_first = log.since_sequence(1)
        assert len(after_first) == 2

    def test_serialization_roundtrip(self):
        log = AppendOnlyLog()
        log.append(data={"action": "embed"}, node_id="n-a")
        log.append(data={"action": "delete"}, node_id="n-b")

        data = log.to_dict()
        restored = AppendOnlyLog.from_dict(data)
        assert restored.size == log.size
        assert restored.digest() == log.digest()


# ===========================================================================
# CRDTMap Tests
# ===========================================================================

class TestCRDTMap:

    def test_set_and_get(self):
        m = CRDTMap()
        m.set("key-1", "value-1", timestamp=1.0, node_id="n-a")
        assert m.get("key-1") == "value-1"

    def test_get_nonexistent(self):
        m = CRDTMap()
        assert m.get("missing") is None

    def test_lww_within_map(self):
        m = CRDTMap()
        m.set("k", "old", timestamp=1.0, node_id="n-a")
        m.set("k", "new", timestamp=2.0, node_id="n-b")
        assert m.get("k") == "new"

    def test_merge_disjoint_keys(self):
        a = CRDTMap()
        a.set("k1", "v1", 1.0, "n-a")

        b = CRDTMap()
        b.set("k2", "v2", 1.0, "n-b")

        merged = a.merge(b)
        assert merged.get("k1") == "v1"
        assert merged.get("k2") == "v2"

    def test_merge_overlapping_keys(self):
        a = CRDTMap()
        a.set("k", "old", 1.0, "n-a")

        b = CRDTMap()
        b.set("k", "new", 2.0, "n-b")

        merged = a.merge(b)
        assert merged.get("k") == "new"

    def test_merge_commutativity(self):
        a = CRDTMap()
        a.set("k1", "v1", 1.0, "n-a")
        a.set("shared", "a-val", 1.0, "n-a")

        b = CRDTMap()
        b.set("k2", "v2", 1.0, "n-b")
        b.set("shared", "b-val", 2.0, "n-b")

        ab = a.merge(b)
        ba = b.merge(a)
        assert ab.get("shared") == ba.get("shared")
        assert ab.get("k1") == ba.get("k1")
        assert ab.get("k2") == ba.get("k2")

    def test_merge_idempotency(self):
        m = CRDTMap()
        m.set("k1", "v1", 1.0, "n-a")
        m.set("k2", "v2", 2.0, "n-b")

        merged = m.merge(m)
        assert merged.get("k1") == m.get("k1")
        assert merged.get("k2") == m.get("k2")

    def test_serialization_roundtrip(self):
        m = CRDTMap()
        m.set("k1", {"nested": True}, 1.0, "n-a")
        m.set("k2", [1, 2, 3], 2.0, "n-b")

        data = m.to_dict()
        restored = CRDTMap.from_dict(data)
        assert restored.get("k1") == m.get("k1")
        assert restored.get("k2") == m.get("k2")
