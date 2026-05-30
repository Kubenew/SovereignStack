"""
SovereignStack CRDT Library — Conflict-Free Replicated Data Types

Implements the CRDT types specified in RFC 0004 (Federation Protocol):
  - LWWRegister:   Last-Writer-Wins register (timestamp + node_id tiebreaker)
  - TombstoneSet:  Set with logical tombstones for delete support
  - AppendOnlyLog: Immutable append-only event sequence
  - CRDTMap:       Recursive per-key merge using nested CRDTs

All types satisfy the CRDT convergence properties:
  - Commutativity:  merge(a, b) == merge(b, a)
  - Associativity:  merge(merge(a, b), c) == merge(a, merge(b, c))
  - Idempotency:    merge(a, a) == a
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# LWW-Register — Last-Writer-Wins Register
# ---------------------------------------------------------------------------

@dataclass
class LWWRegister:
    """
    Last-Writer-Wins Register.

    Conflict resolution: highest timestamp wins.
    Tiebreaker: lexicographic comparison of node_id.
    """

    key: str
    value: Any = None
    timestamp: float = 0.0
    node_id: str = ""

    def set(self, value: Any, timestamp: float, node_id: str) -> None:
        """Set the register value if the write is newer."""
        if self._is_newer(timestamp, node_id):
            self.value = value
            self.timestamp = timestamp
            self.node_id = node_id

    def _is_newer(self, timestamp: float, node_id: str) -> bool:
        if timestamp > self.timestamp:
            return True
        if timestamp == self.timestamp and node_id > self.node_id:
            return True
        return False

    def merge(self, other: LWWRegister) -> LWWRegister:
        """Merge two LWW registers, returning a new register with the winning value."""
        # _is_newer asks: "Is the provided (timestamp, node_id) newer than me?"
        # So self._is_newer(other.timestamp, other.node_id) asks: "Is other newer than self?"
        if self._is_newer(other.timestamp, other.node_id):
            # other wins
            return LWWRegister(
                key=self.key,
                value=other.value,
                timestamp=other.timestamp,
                node_id=other.node_id,
            )
        else:
            # self wins (or equal)
            return LWWRegister(
                key=self.key,
                value=self.value,
                timestamp=self.timestamp,
                node_id=self.node_id,
            )

    def to_dict(self) -> dict:
        return {
            "type": "lww_register",
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LWWRegister:
        return cls(
            key=data["key"],
            value=data.get("value"),
            timestamp=data.get("timestamp", 0.0),
            node_id=data.get("node_id", ""),
        )


# ---------------------------------------------------------------------------
# TombstoneSet — Set with logical tombstones for delete support
# ---------------------------------------------------------------------------

@dataclass
class TombstoneEntry:
    """An entry in the tombstone set with add/remove tracking."""

    element_id: str
    value: Any
    added_at: float = 0.0
    added_by: str = ""
    removed_at: Optional[float] = None
    removed_by: Optional[str] = None

    @property
    def is_alive(self) -> bool:
        """Element is alive if not removed, or if added after removal."""
        if self.removed_at is None:
            return True
        if self.added_at > self.removed_at:
            return True
        if self.added_at == self.removed_at and self.added_by >= (self.removed_by or ""):
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "value": self.value,
            "added_at": self.added_at,
            "added_by": self.added_by,
            "removed_at": self.removed_at,
            "removed_by": self.removed_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TombstoneEntry:
        return cls(
            element_id=data["element_id"],
            value=data["value"],
            added_at=data.get("added_at", 0.0),
            added_by=data.get("added_by", ""),
            removed_at=data.get("removed_at"),
            removed_by=data.get("removed_by"),
        )


@dataclass
class TombstoneSet:
    """
    Set with logical tombstones — supports add and remove with LWW semantics per element.

    Used for vector index entries: upsert = add, delete = tombstone.
    """

    entries: Dict[str, TombstoneEntry] = field(default_factory=dict)

    def add(self, element_id: str, value: Any, timestamp: float, node_id: str) -> None:
        """Add or re-add an element."""
        if element_id in self.entries:
            existing = self.entries[element_id]
            if timestamp > existing.added_at or (
                timestamp == existing.added_at and node_id > existing.added_by
            ):
                existing.value = value
                existing.added_at = timestamp
                existing.added_by = node_id
        else:
            self.entries[element_id] = TombstoneEntry(
                element_id=element_id,
                value=value,
                added_at=timestamp,
                added_by=node_id,
            )

    def remove(self, element_id: str, timestamp: float, node_id: str) -> bool:
        """Tombstone an element. Returns True if element existed."""
        if element_id not in self.entries:
            # Create a tombstoned entry so the deletion propagates
            self.entries[element_id] = TombstoneEntry(
                element_id=element_id,
                value=None,
                added_at=0.0,
                added_by="",
                removed_at=timestamp,
                removed_by=node_id,
            )
            return False

        existing = self.entries[element_id]
        if existing.removed_at is None or timestamp > existing.removed_at or (
            timestamp == existing.removed_at and node_id > (existing.removed_by or "")
        ):
            existing.removed_at = timestamp
            existing.removed_by = node_id
        return True

    def get_alive(self) -> Dict[str, Any]:
        """Return all alive (non-tombstoned) entries as {element_id: value}."""
        return {
            eid: entry.value
            for eid, entry in self.entries.items()
            if entry.is_alive
        }

    def merge(self, other: TombstoneSet) -> TombstoneSet:
        """Merge two tombstone sets, returning a new merged set."""
        merged = TombstoneSet()

        all_ids = set(self.entries.keys()) | set(other.entries.keys())
        for eid in all_ids:
            local = self.entries.get(eid)
            remote = other.entries.get(eid)

            if local is None:
                merged.entries[eid] = TombstoneEntry.from_dict(remote.to_dict())
            elif remote is None:
                merged.entries[eid] = TombstoneEntry.from_dict(local.to_dict())
            else:
                # Merge: take latest add and latest remove independently
                if local.added_at > remote.added_at or (
                    local.added_at == remote.added_at and local.added_by >= remote.added_by
                ):
                    add_at, add_by, value = local.added_at, local.added_by, local.value
                else:
                    add_at, add_by, value = remote.added_at, remote.added_by, remote.value

                # Merge removes
                rem_at, rem_by = None, None
                if local.removed_at is not None and remote.removed_at is not None:
                    if local.removed_at > remote.removed_at or (
                        local.removed_at == remote.removed_at
                        and (local.removed_by or "") >= (remote.removed_by or "")
                    ):
                        rem_at, rem_by = local.removed_at, local.removed_by
                    else:
                        rem_at, rem_by = remote.removed_at, remote.removed_by
                elif local.removed_at is not None:
                    rem_at, rem_by = local.removed_at, local.removed_by
                elif remote.removed_at is not None:
                    rem_at, rem_by = remote.removed_at, remote.removed_by

                merged.entries[eid] = TombstoneEntry(
                    element_id=eid,
                    value=value,
                    added_at=add_at,
                    added_by=add_by,
                    removed_at=rem_at,
                    removed_by=rem_by,
                )

        return merged

    def to_dict(self) -> dict:
        return {
            "type": "tombstone_set",
            "entries": {eid: e.to_dict() for eid, e in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> TombstoneSet:
        ts = cls()
        for eid, entry_data in data.get("entries", {}).items():
            ts.entries[eid] = TombstoneEntry.from_dict(entry_data)
        return ts


# ---------------------------------------------------------------------------
# AppendOnlyLog — Immutable append-only event sequence
# ---------------------------------------------------------------------------

@dataclass
class LogEntry:
    """A single entry in the append-only log."""

    event_id: str
    timestamp: float
    node_id: str
    data: Any
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "data": self.data,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LogEntry:
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            node_id=data["node_id"],
            data=data["data"],
            signature=data.get("signature"),
        )


@dataclass
class AppendOnlyLog:
    """
    Append-only log — entries are never deleted or modified.

    Merge = set union of all entries, deduplicated by event_id,
    ordered by (timestamp, node_id, event_id).
    """

    _entries: Dict[str, LogEntry] = field(default_factory=dict)

    def append(self, data: Any, node_id: str, signature: Optional[str] = None) -> LogEntry:
        """Append a new entry. Returns the created LogEntry."""
        entry = LogEntry(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            node_id=node_id,
            data=data,
            signature=signature,
        )
        self._entries[entry.event_id] = entry
        return entry

    def add_entry(self, entry: LogEntry) -> bool:
        """Add an existing entry (from remote sync). Returns True if new."""
        if entry.event_id in self._entries:
            return False
        self._entries[entry.event_id] = entry
        return True

    def entries(self) -> List[LogEntry]:
        """Return all entries sorted by (timestamp, node_id, event_id)."""
        return sorted(
            self._entries.values(),
            key=lambda e: (e.timestamp, e.node_id, e.event_id),
        )

    def since_sequence(self, since: int) -> List[LogEntry]:
        """Return entries from index `since` onward in sorted order."""
        return self.entries()[since:]

    @property
    def size(self) -> int:
        return len(self._entries)

    def digest(self) -> str:
        """Compute a SHA-256 digest over the sorted log for anti-entropy comparison."""
        entries = self.entries()
        content = json.dumps(
            [e.event_id for e in entries],
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def merge(self, other: AppendOnlyLog) -> AppendOnlyLog:
        """Merge two append-only logs (set union by event_id)."""
        merged = AppendOnlyLog()
        merged._entries = {**self._entries, **other._entries}
        return merged

    def to_dict(self) -> dict:
        return {
            "type": "append_only_log",
            "entries": {eid: e.to_dict() for eid, e in self._entries.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppendOnlyLog:
        log = cls()
        for eid, entry_data in data.get("entries", {}).items():
            log._entries[eid] = LogEntry.from_dict(entry_data)
        return log


# ---------------------------------------------------------------------------
# CRDTMap — Recursive per-key merge
# ---------------------------------------------------------------------------

@dataclass
class CRDTMap:
    """
    Recursive CRDT Map — each key maps to a LWW-Register.

    For more complex nested CRDTs, values can be serialized CRDT state.
    This is the building block for policy sync and node metadata.
    """

    registers: Dict[str, LWWRegister] = field(default_factory=dict)

    def set(self, key: str, value: Any, timestamp: float, node_id: str) -> None:
        """Set a key using LWW semantics."""
        if key in self.registers:
            self.registers[key].set(value, timestamp, node_id)
        else:
            self.registers[key] = LWWRegister(
                key=key,
                value=value,
                timestamp=timestamp,
                node_id=node_id,
            )

    def get(self, key: str) -> Any:
        """Get the current value for a key, or None."""
        reg = self.registers.get(key)
        return reg.value if reg else None

    def keys(self) -> Set[str]:
        return set(self.registers.keys())

    def merge(self, other: CRDTMap) -> CRDTMap:
        """Merge two CRDT maps, merging registers per-key."""
        merged = CRDTMap()
        all_keys = set(self.registers.keys()) | set(other.registers.keys())

        for key in all_keys:
            local = self.registers.get(key)
            remote = other.registers.get(key)

            if local is None:
                merged.registers[key] = LWWRegister.from_dict(remote.to_dict())
            elif remote is None:
                merged.registers[key] = LWWRegister.from_dict(local.to_dict())
            else:
                merged.registers[key] = local.merge(remote)

        return merged

    def to_dict(self) -> dict:
        return {
            "type": "crdt_map",
            "registers": {k: r.to_dict() for k, r in self.registers.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> CRDTMap:
        m = cls()
        for key, reg_data in data.get("registers", {}).items():
            m.registers[key] = LWWRegister.from_dict(reg_data)
        return m
