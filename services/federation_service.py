from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, Field
import os
import requests
import uuid
import logging
import time
from typing import List, Dict, Optional

from services.event_log import EventLog, EventSigner
from services.sync_engine import SyncEngine, SyncMessage, MessageType

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background sync loop lifecycle."""
    sync_engine.start()
    logger.info("Federation service started: node=%s jurisdiction=%s", NODE_ID, JURISDICTION)
    yield
    sync_engine.stop()
    logger.info("Federation service shutting down")

app = FastAPI(title="SovereignStack Federation Relay", version="2026.3", lifespan=lifespan)

NODE_ID = os.getenv("NODE_ID", str(uuid.uuid4()))
KNOWN_PEERS = os.getenv("KNOWN_PEERS", "").split(",")
FEDERATION_TOKEN = os.getenv("FEDERATION_TOKEN", "default-federation-token")
JURISDICTION = os.getenv("JURISDICTION", "GLOBAL")
SYNC_INTERVAL = float(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

# ---------------------------------------------------------------------------
# Initialize Event Log and Sync Engine
# ---------------------------------------------------------------------------

_signer = EventSigner(
    private_key_path=os.getenv("EVENT_SIGNING_KEY"),
    hmac_secret=os.getenv("EVENT_SIGNING_SECRET"),
)

event_log = EventLog(
    node_id=NODE_ID,
    data_dir=os.path.join(DATA_DIR, "events"),
    signer=_signer,
    jurisdiction=JURISDICTION,
)

sync_engine = SyncEngine(
    node_id=NODE_ID,
    event_log=event_log,
    jurisdiction=JURISDICTION,
    sync_interval=SYNC_INTERVAL,
)


# ---------------------------------------------------------------------------
# HTTP transport for sync engine
# ---------------------------------------------------------------------------

def _http_transport(endpoint: str, message: dict) -> Optional[dict]:
    """Send a sync message to a peer via HTTP and return the response."""
    try:
        url = f"{endpoint}/mesh/sync"
        resp = requests.post(
            url,
            json=message,
            headers={"Authorization": f"Bearer {FEDERATION_TOKEN}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("Transport error to %s: %s", endpoint, exc)
        return None


sync_engine.set_transport(_http_transport)


# ---------------------------------------------------------------------------
# Register known peers on startup
# ---------------------------------------------------------------------------

for peer_config in KNOWN_PEERS:
    peer_config = peer_config.strip()
    if not peer_config:
        continue
    # Format: peer_id=endpoint or just endpoint
    if "=" in peer_config:
        pid, endpoint = peer_config.split("=", 1)
    else:
        pid = f"peer-{peer_config.replace(':', '-').replace('/', '-')}"
        endpoint = peer_config
    sync_engine.add_peer(pid, endpoint, JURISDICTION)


# ---------------------------------------------------------------------------
# Legacy Models (preserved for backward compatibility)
# ---------------------------------------------------------------------------

class FederationPing(BaseModel):
    node_id: str
    status: str
    timestamp: float

class MeshRoute(BaseModel):
    destination_node: str
    next_hop: str
    cost: int

routing_table: Dict[str, MeshRoute] = {}
active_peers: set = set()


# ---------------------------------------------------------------------------
# Legacy Endpoints (preserved)
# ---------------------------------------------------------------------------

@app.post("/mesh/ping")
def receive_ping(ping: FederationPing, authorization: str | None = Header(None)):
    if authorization != f"Bearer {FEDERATION_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized Federation Node")
    
    active_peers.add(ping.node_id)
    return {"status": "ack", "node_id": NODE_ID}

@app.get("/mesh/peers")
def list_peers():
    sync_peers = sync_engine.get_peers()
    return {
        "active_peers": list(active_peers),
        "known_peers": KNOWN_PEERS,
        "sync_peers": [
            {
                "peer_id": p.peer_id,
                "endpoint": p.endpoint,
                "jurisdiction": p.jurisdiction,
                "healthy": p.is_healthy,
                "last_sync": p.last_sync_time,
            }
            for p in sync_peers
        ],
    }

@app.post("/mesh/route/update")
def update_route(route: MeshRoute, authorization: str | None = Header(None)):
    if authorization != f"Bearer {FEDERATION_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized Federation Node")
    
    if route.destination_node not in routing_table or routing_table[route.destination_node].cost > route.cost:
        routing_table[route.destination_node] = route
        return {"status": "route_accepted"}
    return {"status": "route_ignored"}

@app.post("/mesh/relay/{target_node}")
def relay_payload(target_node: str, request: Request, authorization: str | None = Header(None)):
    if authorization != f"Bearer {FEDERATION_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized Federation Node")
        
    if target_node == NODE_ID:
        # process locally (mocked)
        return {"status": "processed_locally"}
        
    if target_node not in routing_table:
        raise HTTPException(status_code=404, detail="Route to target node unknown")
        
    next_hop = routing_table[target_node].next_hop
    # In a real scenario, we would forward the request to next_hop here.
    return {"status": "relayed", "next_hop": next_hop}


# ---------------------------------------------------------------------------
# New Sync Endpoints (RFC 0004)
# ---------------------------------------------------------------------------

class SyncRequest(BaseModel):
    """Pydantic model for incoming sync messages."""
    protocol_version: str = "1.0"
    message_type: str
    node_id: str = ""
    session_id: str = ""
    state_digest: str = ""
    since_sequence: int = 0
    batch_size: int = 100
    jurisdiction: str = "GLOBAL"
    events: list = []
    error: Optional[str] = None


@app.post("/mesh/sync")
def handle_sync(req: SyncRequest, authorization: str | None = Header(None)):
    """
    Unified sync endpoint — handles SYNC_REQUEST, SYNC_ACK, EVENTS messages.
    Implements the sync protocol from RFC 0004.
    """
    if authorization != f"Bearer {FEDERATION_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized Federation Node")

    message = SyncMessage.from_dict(req.model_dump())
    response = sync_engine.handle_message(message)
    return response.to_dict()


@app.post("/mesh/events")
def receive_events(req: SyncRequest, authorization: str | None = Header(None)):
    """
    Receive a batch of events from a peer (used for push-based sync).
    """
    if authorization != f"Bearer {FEDERATION_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized Federation Node")

    message = SyncMessage(
        message_type=MessageType.EVENTS,
        node_id=req.node_id,
        session_id=req.session_id,
        events=req.events,
        jurisdiction=req.jurisdiction,
    )

    response = sync_engine.handle_events(message)
    return response.to_dict()


@app.get("/mesh/sync/status")
def sync_status():
    """Return the current sync engine status."""
    return sync_engine.status()


@app.get("/mesh/events/log")
def event_log_query(
    since_sequence: int = 0,
    event_type: Optional[str] = None,
    limit: int = 100,
):
    """Query the local event log."""
    events = event_log.get_events(
        since_sequence=since_sequence,
        event_type=event_type,
        limit=limit,
    )
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
        "local_sequence": event_log.local_sequence,
        "digest": event_log.digest(),
    }


# ---------------------------------------------------------------------------
# Federated Agent Messaging
# ---------------------------------------------------------------------------

class AgentMessage(BaseModel):
    source_agent_id: str
    target_agent_id: str
    target_node_id: str
    payload: dict
    timestamp: float = Field(default_factory=time.time)

@app.post("/mesh/agent/message")
def route_agent_message(msg: AgentMessage, authorization: str | None = Header(None)):
    """
    Route a message to an agent on this node or forward to another node.
    """
    if authorization != f"Bearer {FEDERATION_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized Federation Node")
        
    if msg.target_node_id == NODE_ID:
        # Deliver locally to agent_service via internal DNS (mocked here)
        logger.info(f"Delivering message to local agent {msg.target_agent_id}")
        # In a real cluster: requests.post(f"http://agent-service:8084/v1/agents/{msg.target_agent_id}/messages", json=msg.model_dump())
        return {"status": "delivered_locally"}
        
    # Forward to peer
    peer = next((p for p in sync_engine.get_peers() if p.peer_id == msg.target_node_id), None)
    if not peer:
        raise HTTPException(status_code=404, detail="Target node not found in federation mesh")
        
    try:
        url = f"{peer.endpoint}/mesh/agent/message"
        resp = requests.post(
            url,
            json=msg.model_dump(),
            headers={"Authorization": f"Bearer {FEDERATION_TOKEN}"},
            timeout=5,
        )
        resp.raise_for_status()
        return {"status": "relayed", "next_hop": msg.target_node_id}
    except Exception as exc:
        logger.error(f"Failed to relay agent message: {exc}")
        raise HTTPException(status_code=502, detail="Bad Gateway to target node")


# ---------------------------------------------------------------------------
# Health and Lifecycle
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "federation_relay",
        "node_id": NODE_ID,
        "jurisdiction": JURISDICTION,
        "sync_running": sync_engine._running,
        "event_count": event_log.event_count,
    }


# Startup/shutdown are now handled by lifespan


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
