from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import uuid
import time
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

app = FastAPI(title="OASA Secure Weight Federation", version="2026.3")

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
NODE_ID = os.getenv("NODE_ID", str(uuid.uuid4()))
SHARD_ENCRYPTION_KEY = os.getenv("SHARD_ENCRYPTION_KEY", "")
SHARD_MANIFEST_FILE = os.path.join(DATA_DIR, "shard_manifest.json")
SHARD_DIR = os.path.join(DATA_DIR, "shards")

os.makedirs(SHARD_DIR, exist_ok=True)


def _get_cipher():
    if SHARD_ENCRYPTION_KEY:
        key = base64.urlsafe_b64encode(hashlib.sha256(SHARD_ENCRYPTION_KEY.encode()).digest())
    else:
        key = Fernet.generate_key()
    return Fernet(key)


def _load_manifest():
    try:
        with open(SHARD_MANIFEST_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"shards": [], "topology": {}}


def _save_manifest(data):
    os.makedirs(os.path.dirname(SHARD_MANIFEST_FILE), exist_ok=True)
    with open(SHARD_MANIFEST_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


class ShardRegistration(BaseModel):
    model_name: str
    model_version: str = "1.0.0"
    shard_index: int
    total_shards: int
    layers: list[str]
    node_endpoint: str
    input_shape: list[int] = []
    output_shape: list[int] = []


class InferenceRequest(BaseModel):
    model_name: str
    model_version: str = "1.0.0"
    input_data: list[list[float]]
    request_id: str = ""


class ShardInferenceForward(BaseModel):
    shard_index: int
    activations: list[list[float]]
    request_id: str
    session_id: str


class WeightShardData(BaseModel):
    shard_id: str
    weights_b64: str
    metadata: dict = {}


class ShardHealthUpdate(BaseModel):
    node_endpoint: str
    shard_id: str
    healthy: bool
    load: float = 0.0


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "weight_federation",
        "node_id": NODE_ID,
        "shard_count": len(_load_manifest()["shards"]),
    }


@app.get("/federation/weights/manifest")
def get_manifest():
    return _load_manifest()


@app.post("/federation/weights/register")
def register_shard(req: ShardRegistration):
    manifest = _load_manifest()
    shard_id = f"{req.model_name}-v{req.model_version}-shard-{req.shard_index}"
    for s in manifest["shards"]:
        if s["shard_id"] == shard_id:
            s["node_endpoint"] = req.node_endpoint
            s["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_manifest(manifest)
            return {"status": "updated", "shard_id": shard_id}
    entry = {
        "shard_id": shard_id,
        "model_name": req.model_name,
        "model_version": req.model_version,
        "shard_index": req.shard_index,
        "total_shards": req.total_shards,
        "layers": req.layers,
        "node_endpoint": req.node_endpoint,
        "input_shape": req.input_shape,
        "output_shape": req.output_shape,
        "healthy": True,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest["shards"].append(entry)
    topology_key = f"{req.model_name}@v{req.model_version}"
    if topology_key not in manifest["topology"]:
        manifest["topology"][topology_key] = {
            "model_name": req.model_name,
            "model_version": req.model_version,
            "total_shards": req.total_shards,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    _save_manifest(manifest)
    return {"status": "registered", "shard_id": shard_id}


@app.post("/federation/weights/store")
def store_weight_shard(req: WeightShardData):
    cipher = _get_cipher()
    encrypted = cipher.encrypt(req.weights_b64.encode())
    shard_path = os.path.join(SHARD_DIR, f"{req.shard_id}.enc")
    with open(shard_path, "wb") as f:
        f.write(encrypted)
    checksum = hashlib.sha256(encrypted).hexdigest()
    manifest = _load_manifest()
    for s in manifest["shards"]:
        if s["shard_id"] == req.shard_id:
            s["stored"] = True
            s["checksum"] = checksum
            s["metadata"] = req.metadata
            break
    _save_manifest(manifest)
    return {"status": "stored", "shard_id": req.shard_id, "checksum": checksum}


@app.post("/federation/weights/inference")
def run_sharded_inference(req: InferenceRequest):
    manifest = _load_manifest()
    topology_key = f"{req.model_name}@v{req.model_version}"
    topology = manifest["topology"].get(topology_key)
    if not topology:
        raise HTTPException(404, f"No weight topology found for {topology_key}")
    total_shards = topology["total_shards"]
    shards = sorted(
        [s for s in manifest["shards"] if s["model_name"] == req.model_name
         and s["model_version"] == req.model_version and s.get("healthy", False)],
        key=lambda s: s["shard_index"],
    )
    if len(shards) != total_shards:
        raise HTTPException(503, f"Only {len(shards)}/{total_shards} shards healthy")

    rid = req.request_id or str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    activations = req.input_data

    for shard in shards:
        endpoint = shard["node_endpoint"]
        try:
            import requests
            resp = requests.post(
                f"{endpoint}/federation/weights/forward",
                json={
                    "shard_index": shard["shard_index"],
                    "activations": activations,
                    "request_id": rid,
                    "session_id": session_id,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                raise HTTPException(502, f"Shard {shard['shard_index']} failed: {resp.text}")
            activations = resp.json()["activations"]
        except requests.ConnectionError:
            raise HTTPException(502, f"Shard {shard['shard_index']} at {endpoint} unreachable")

    return {
        "request_id": rid,
        "session_id": session_id,
        "model": f"{req.model_name}@v{req.model_version}",
        "shards_used": total_shards,
        "output": activations,
    }


@app.post("/federation/weights/forward")
def forward_shard(req: ShardInferenceForward):
    shard_path = os.path.join(SHARD_DIR, f"{req.session_id}-{req.shard_index}.enc")
    if not os.path.exists(shard_path):
        manifest = _load_manifest()
        shard_id = f"{req.session_id.split('-')[0]}-shard-{req.shard_index}"
        for s in manifest["shards"]:
            if s["shard_index"] == req.shard_index:
                shard_path = os.path.join(SHARD_DIR, f"{s['shard_id']}.enc")
                break
    if not os.path.exists(shard_path):
        raise HTTPException(404, f"Weight shard {req.shard_index} not found on this node")

    cipher = _get_cipher()
    with open(shard_path, "rb") as f:
        encrypted = f.read()
    try:
        weights_json = cipher.decrypt(encrypted).decode()
    except Exception:
        raise HTTPException(500, "Failed to decrypt weight shard")

    weights = json.loads(weights_json)
    import numpy as np
    weights_matrix = np.array(weights, dtype=np.float32)
    input_matrix = np.array(req.activations, dtype=np.float32)
    output = np.dot(input_matrix, weights_matrix.T).tolist()

    return {
        "shard_index": req.shard_index,
        "request_id": req.request_id,
        "session_id": req.session_id,
        "activations": output,
    }


@app.post("/federation/weights/health")
def report_shard_health(req: ShardHealthUpdate):
    manifest = _load_manifest()
    for s in manifest["shards"]:
        if s["shard_id"] == req.shard_id:
            s["healthy"] = req.healthy
            s["load"] = req.load
            s["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            _save_manifest(manifest)
            return {"status": "updated", "shard_id": req.shard_id, "healthy": req.healthy}
    raise HTTPException(404, f"Shard {req.shard_id} not found")


@app.get("/federation/weights/shard/{shard_id}")
def get_shard_info(shard_id: str):
    manifest = _load_manifest()
    for s in manifest["shards"]:
        if s["shard_id"] == shard_id:
            result = {k: v for k, v in s.items() if k != "stored"}
            result["has_weights"] = os.path.exists(os.path.join(SHARD_DIR, f"{shard_id}.enc"))
            return result
    raise HTTPException(404, f"Shard {shard_id} not found")


@app.get("/federation/weights/status")
def federation_status():
    manifest = _load_manifest()
    total = len(manifest["shards"])
    healthy = sum(1 for s in manifest["shards"] if s.get("healthy", False))
    stored = sum(1 for s in manifest["shards"] if s.get("stored", False))
    return {
        "node_id": NODE_ID,
        "total_shards": total,
        "healthy_shards": healthy,
        "stored_shards": stored,
        "topologies": list(manifest["topology"].keys()),
        "models": list(set(s["model_name"] for s in manifest["shards"])),
    }
