"""
SovereignStack KV Cache Service — Context Cache with TTL and CRDT Sync

Implements the KV Cache subsystem from RFC 0006 (Memory Specification):
  - POST /cache/set   — Store context with TTL
  - GET  /cache/get   — Retrieve context by session_id
  - POST /cache/clear — Expire all entries for org
  - TTL enforcement with background reaper
  - CRDT-aware: emits cache.set events for cross-node sync
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from services.spiffe_auth import authorized_spiffe_ids, spiffe_enabled

logger = logging.getLogger(__name__)

app = FastAPI(title="OASA KV Cache Service", version="2026.3")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
MAX_TTL_SECONDS = int(os.getenv("CACHE_MAX_TTL", "86400"))  # 24h per RFC 0006
REAPER_INTERVAL = int(os.getenv("CACHE_REAPER_INTERVAL", "60"))

# Event log integration (set externally by the app bootstrap)
_event_log = None


def set_event_log(event_log) -> None:
    """Inject the EventLog for CRDT event emission."""
    global _event_log
    _event_log = event_log


# ---------------------------------------------------------------------------
# SPIFFE auth for inter-service calls
# ---------------------------------------------------------------------------

_cache_auth = authorized_spiffe_ids(
    allowed=[
        "spiffe://sovereign.stack/service/gateway",
        "spiffe://sovereign.stack/service/memory",
        "spiffe://sovereign.stack/service/ingest",
        "spiffe://sovereign.stack/service/admin",
    ]
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class CacheSetRequest(BaseModel):
    session_id: str
    context: str
    org_id: str = "default"
    ttl_seconds: Optional[int] = None  # defaults to DEFAULT_TTL_SECONDS


class CacheGetRequest(BaseModel):
    session_id: str
    org_id: str = "default"


class CacheClearRequest(BaseModel):
    org_id: str = "default"


class CacheEntry:
    """A single entry in the KV cache with TTL tracking."""

    def __init__(
        self,
        session_id: str,
        context: str,
        org_id: str,
        ttl_until: float,
        created_at: float,
        node_id: str = "",
    ):
        self.session_id = session_id
        self.context = context
        self.org_id = org_id
        self.ttl_until = ttl_until
        self.created_at = created_at
        self.node_id = node_id

    @property
    def is_expired(self) -> bool:
        return time.time() > self.ttl_until

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "context": self.context,
            "org_id": self.org_id,
            "ttl_until": self.ttl_until,
            "created_at": self.created_at,
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CacheEntry:
        return cls(
            session_id=data["session_id"],
            context=data["context"],
            org_id=data["org_id"],
            ttl_until=data["ttl_until"],
            created_at=data["created_at"],
            node_id=data.get("node_id", ""),
        )


# ---------------------------------------------------------------------------
# In-memory cache store with disk persistence
# ---------------------------------------------------------------------------

class CacheStore:
    """Thread-safe KV cache with TTL enforcement."""

    def __init__(self, cache_dir: str):
        self._entries: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._cache_dir = cache_dir
        self._load_from_disk()

        # Start background reaper
        self._reaper_running = True
        self._reaper_thread = threading.Thread(
            target=self._reaper_loop, daemon=True, name="cache-reaper"
        )
        self._reaper_thread.start()

    def _load_from_disk(self) -> None:
        """Load persisted cache entries from disk on startup."""
        if not os.path.exists(self._cache_dir):
            return

        loaded = 0
        for fn in os.listdir(self._cache_dir):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self._cache_dir, fn), "r", encoding="utf-8") as f:
                    data = json.load(f)
                entry = CacheEntry.from_dict(data)
                if not entry.is_expired:
                    self._entries[entry.session_id] = entry
                    loaded += 1
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Skipping corrupt cache entry %s: %s", fn, exc)

        logger.info("Loaded %d cache entries from disk", loaded)

    def set(self, entry: CacheEntry) -> None:
        """Store or update a cache entry."""
        with self._lock:
            self._entries[entry.session_id] = entry
            self._persist(entry)

    def get(self, session_id: str, org_id: str) -> Optional[CacheEntry]:
        """Retrieve a cache entry by session_id and org_id."""
        with self._lock:
            entry = self._entries.get(session_id)
            if entry is None:
                return None
            if entry.org_id != org_id:
                return None
            if entry.is_expired:
                self._evict(session_id)
                return None
            return entry

    def clear_org(self, org_id: str) -> int:
        """Remove all entries for an org. Returns count of removed entries."""
        with self._lock:
            to_remove = [
                sid for sid, entry in self._entries.items() if entry.org_id == org_id
            ]
            for sid in to_remove:
                self._evict(sid)
            return len(to_remove)

    def _persist(self, entry: CacheEntry) -> None:
        """Write entry to disk."""
        try:
            path = os.path.join(self._cache_dir, f"{entry.session_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f)
        except OSError as exc:
            logger.error("Failed to persist cache entry: %s", exc)

    def _evict(self, session_id: str) -> None:
        """Remove entry from memory and disk."""
        self._entries.pop(session_id, None)
        path = os.path.join(self._cache_dir, f"{session_id}.json")
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def _reaper_loop(self) -> None:
        """Background thread: periodically evict expired entries."""
        while self._reaper_running:
            try:
                with self._lock:
                    expired = [
                        sid
                        for sid, entry in self._entries.items()
                        if entry.is_expired
                    ]
                    for sid in expired:
                        self._evict(sid)
                    if expired:
                        logger.info("Reaped %d expired cache entries", len(expired))
            except Exception as exc:
                logger.error("Cache reaper error: %s", exc)

            time.sleep(REAPER_INTERVAL)

    def stats(self) -> dict:
        """Return cache statistics."""
        with self._lock:
            alive = sum(1 for e in self._entries.values() if not e.is_expired)
            return {
                "total_entries": len(self._entries),
                "alive_entries": alive,
                "expired_entries": len(self._entries) - alive,
            }

    def stop(self) -> None:
        self._reaper_running = False


# Global store instance
_store = CacheStore(CACHE_DIR)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/cache/set")
def cache_set(req: CacheSetRequest, identity: dict = Depends(_cache_auth)):
    """Store context with TTL."""
    ttl = req.ttl_seconds or DEFAULT_TTL_SECONDS
    ttl = min(ttl, MAX_TTL_SECONDS)

    now = time.time()
    entry = CacheEntry(
        session_id=req.session_id,
        context=req.context,
        org_id=req.org_id,
        ttl_until=now + ttl,
        created_at=now,
        node_id=os.getenv("NODE_ID", "local"),
    )

    _store.set(entry)

    # Emit CRDT event for cross-node sync
    if _event_log is not None:
        _event_log.emit("cache.set", {
            "session_id": req.session_id,
            "org_id": req.org_id,
            "context_hash": str(hash(req.context)),
            "ttl_seconds": ttl,
        })

    logger.info(
        "Cache set: session=%s org=%s ttl=%ds by %s",
        req.session_id,
        req.org_id,
        ttl,
        identity.get("spiffe_id", "unknown"),
    )

    return {
        "status": "stored",
        "session_id": req.session_id,
        "ttl_seconds": ttl,
    }


@app.post("/cache/get")
def cache_get(req: CacheGetRequest, identity: dict = Depends(_cache_auth)):
    """Retrieve context by session_id."""
    entry = _store.get(req.session_id, req.org_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Cache entry not found or expired")

    return {
        "session_id": entry.session_id,
        "context": entry.context,
        "org_id": entry.org_id,
        "ttl_until": entry.ttl_until,
        "created_at": entry.created_at,
    }


@app.post("/cache/clear")
def cache_clear(req: CacheClearRequest, identity: dict = Depends(_cache_auth)):
    """Expire all entries for org."""
    removed = _store.clear_org(req.org_id)
    logger.info(
        "Cache cleared for org=%s (%d entries) by %s",
        req.org_id,
        removed,
        identity.get("spiffe_id", "unknown"),
    )
    return {"status": "cleared", "org_id": req.org_id, "entries_removed": removed}


@app.get("/cache/stats")
def cache_stats():
    """Return cache statistics."""
    return _store.stats()


@app.get("/health")
def health():
    return {"status": "ok", "service": "kv_cache", "spiffe_enabled": spiffe_enabled()}
