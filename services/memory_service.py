from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from services.spiffe_auth import authorized_spiffe_ids, spiffe_enabled
import os, json, uuid, logging, time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

app = FastAPI(title="OASA Memory Service", version="2026.3")

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

NODE_ID = os.getenv("NODE_ID", "local")

# ---------------------------------------------------------------------------
# Event log integration for CRDT sync
# ---------------------------------------------------------------------------

_event_log = None


def set_event_log(event_log) -> None:
    """Inject the EventLog for CRDT event emission."""
    global _event_log
    _event_log = event_log


def _emit_event(event_type: str, data: dict) -> None:
    """Emit a CRDT event if the event log is available."""
    if _event_log is not None:
        try:
            _event_log.emit(event_type, data)
        except Exception as exc:
            logger.error("Failed to emit event %s: %s", event_type, exc)


# ---------------------------------------------------------------------------
# SPIFFE auth
# ---------------------------------------------------------------------------

# Services that may call memory (gateway, ingest, other nodes)
_memory_auth = authorized_spiffe_ids(
    allowed=[
        "spiffe://sovereign.stack/service/gateway",
        "spiffe://sovereign.stack/service/ingest",
        "spiffe://sovereign.stack/service/admin",
    ]
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class EmbedRequest(BaseModel):
    doc_id: str
    text: str
    org_id: str = "default"
    metadata: Optional[Dict[str, Any]] = None
    ttl_seconds: Optional[int] = None


class QueryRequest(BaseModel):
    query: str
    org_id: str = "default"
    top_k: int = 3
    min_score: Optional[float] = None
    filter: Optional[Dict[str, Any]] = None


class DeleteRequest(BaseModel):
    doc_id: str
    org_id: str = "default"


class ClearRequest(BaseModel):
    org_id: str = "default"
    confirm: bool = False


# ---------------------------------------------------------------------------
# Vector Store endpoints
# ---------------------------------------------------------------------------

@app.post("/embed")
def embed(req: EmbedRequest, identity: dict = Depends(_memory_auth)):
    """Store document embedding (RFC 0006: POST /embed)."""
    item_id = str(uuid.uuid4())
    now = time.time()
    record = {
        "id": item_id,
        "doc_id": req.doc_id,
        "org_id": req.org_id,
        "text": req.text,
        "metadata": req.metadata or {},
        "created_at": now,
        "ttl_seconds": req.ttl_seconds,
        "node_id": NODE_ID,
    }
    with open(os.path.join(MEMORY_DIR, f"{item_id}.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    # Emit CRDT event for cross-node sync
    _emit_event("memory.vector.upsert", {
        "doc_id": req.doc_id,
        "item_id": item_id,
        "org_id": req.org_id,
    })

    logger.info("Stored doc %s (item=%s) by %s", req.doc_id, item_id, identity.get("spiffe_id", "unknown"))
    return {"status": "stored", "id": item_id, "doc_id": req.doc_id}


@app.post("/query")
def query(req: QueryRequest, identity: dict = Depends(_memory_auth)):
    """Semantic search — top-k retrieval (RFC 0006: POST /query)."""
    matches = []
    for fn in os.listdir(MEMORY_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(MEMORY_DIR, fn), "r", encoding="utf-8") as f:
                rec = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        if rec.get("org_id") != req.org_id:
            continue

        # Check TTL expiration
        if rec.get("ttl_seconds") is not None:
            created = rec.get("created_at", 0)
            if time.time() > created + rec["ttl_seconds"]:
                continue

        # Apply metadata filter if provided
        if req.filter:
            record_meta = rec.get("metadata", {})
            if not all(record_meta.get(k) == v for k, v in req.filter.items()):
                continue

        # Text matching (naive — will be replaced by vector similarity)
        if req.query.lower() in rec.get("text", "").lower():
            matches.append(rec)

    matches = matches[:req.top_k]
    context = "\n\n".join([m.get("text", "") for m in matches])
    return {"matches": matches, "context": context, "count": len(matches)}


@app.delete("/embed")
def delete_embed(req: DeleteRequest, identity: dict = Depends(_memory_auth)):
    """Remove a document from the vector store (RFC 0006: DELETE /embed)."""
    removed = 0
    for fn in os.listdir(MEMORY_DIR):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(MEMORY_DIR, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            if rec.get("doc_id") == req.doc_id and rec.get("org_id") == req.org_id:
                os.remove(path)
                removed += 1
        except (json.JSONDecodeError, OSError):
            continue

    if removed == 0:
        raise HTTPException(status_code=404, detail="Document not found")

    # Emit CRDT event for cross-node sync
    _emit_event("memory.vector.delete", {
        "doc_id": req.doc_id,
        "org_id": req.org_id,
    })

    logger.info("Deleted doc %s (org=%s, count=%d) by %s", req.doc_id, req.org_id, removed, identity.get("spiffe_id", "unknown"))
    return {"status": "deleted", "doc_id": req.doc_id, "items_removed": removed}


@app.post("/clear")
def clear_vectors(req: ClearRequest, identity: dict = Depends(_memory_auth)):
    """Clear all vectors for an org (RFC 0006: POST /clear — admin only)."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to clear all vectors")

    removed = 0
    for fn in os.listdir(MEMORY_DIR):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(MEMORY_DIR, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            if rec.get("org_id") == req.org_id:
                os.remove(path)
                removed += 1
        except (json.JSONDecodeError, OSError):
            continue

    logger.info("Cleared %d vectors for org=%s by %s", removed, req.org_id, identity.get("spiffe_id", "unknown"))
    return {"status": "cleared", "org_id": req.org_id, "items_removed": removed}


@app.post("/backup")
def backup(identity: dict = Depends(_memory_auth)):
    """Trigger snapshot backup of vector store (RFC 0006: POST /backup)."""
    import shutil
    backup_dir = os.path.join(DATA_DIR, "memory_backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_name = f"backup-{int(time.time())}"
    backup_path = os.path.join(backup_dir, backup_name)
    shutil.copytree(MEMORY_DIR, backup_path)

    file_count = len([f for f in os.listdir(backup_path) if f.endswith(".json")])
    logger.info("Backup created: %s (%d files)", backup_name, file_count)
    return {
        "status": "backed_up",
        "backup_name": backup_name,
        "file_count": file_count,
    }


# ---------------------------------------------------------------------------
# Events query endpoint
# ---------------------------------------------------------------------------

@app.get("/events")
def get_events(
    since: Optional[float] = None,
    until: Optional[float] = None,
    actor: Optional[str] = None,
    limit: int = 100,
):
    """Query memory events (RFC 0006: GET /events)."""
    if _event_log is None:
        return {"events": [], "note": "Event log not configured"}

    events = _event_log.get_events(
        event_type=None,  # all memory events
        since_timestamp=since,
        until_timestamp=until,
        limit=limit,
    )

    # Filter to memory events only
    memory_events = [
        e.to_dict() for e in events
        if e.event_type.startswith("memory.")
    ]

    return {"events": memory_events, "count": len(memory_events)}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    file_count = len([f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")])
    return {
        "status": "ok",
        "service": "memory",
        "spiffe_enabled": spiffe_enabled(),
        "vector_count": file_count,
        "event_log_connected": _event_log is not None,
    }
