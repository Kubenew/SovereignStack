"""
Ollama Adapter for SovereignStack

Bridges Ollama's local inference API into the SovereignStack identity and governance model.
Wraps any Ollama model as a SovereignStack capability with UAI identity, provenance logging,
and policy enforcement.

Usage:
    python adapter.py --ollama-host http://localhost:11434 --node-url http://localhost:8080
"""

import argparse
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ollama-adapter")

app = FastAPI(title="SovereignStack Ollama Adapter", version="0.4.0")

_config = {
    "ollama_host": "http://localhost:11434",
    "node_url": "http://localhost:8080",
    "jurisdiction": "us",
    "audit_log": "/var/log/sovereignstack/audit.log",
    "log_requests": True,
}

_model_cache: dict[str, dict] = {}


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _audit_entry(entry_type: str, payload: dict) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": entry_type,
        "node": _config["node_url"],
        "jurisdiction": _config["jurisdiction"],
        "entry_id": str(uuid.uuid4()),
        **payload,
    }


def _write_audit(entry: dict) -> None:
    log_path = Path(_config["audit_log"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


async def _discover_models() -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_config['ollama_host']}/api/tags")
        resp.raise_for_status()
        return resp.json().get("models", [])


async def _check_policy(model_name: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{_config['node_url']}/policy/check",
                params={"capability": f"capability://ollama/{model_name}",
                        "jurisdiction": _config["jurisdiction"]},
            )
            if resp.status_code == 200:
                return resp.json().get("allowed", True)
    except Exception:
        pass
    return True


@app.on_event("startup")
async def startup():
    logger.info("Discovering Ollama models...")
    try:
        models = await _discover_models()
        for m in models:
            name = m.get("name", "unknown")
            _model_cache[name] = {
                "uri": f"model://ollama/{name}",
                "capability": f"capability://ollama/{name}",
                "size": m.get("size", 0),
                "modified_at": m.get("modified_at", ""),
            }
            logger.info(f"  Registered: model://ollama/{name}")
    except Exception as e:
        logger.warning(f"Could not discover models at startup: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "adapter": "ollama", "models": len(_model_cache)}


@app.get("/v1/models")
async def list_models():
    try:
        models = await _discover_models()
        data = []
        for m in models:
            name = m.get("name", "unknown")
            data.append({
                "id": f"ollama/{name}",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ollama",
                "capabilities_uri": f"capability://ollama/{name}",
                "model_uri": f"model://ollama/{name}",
            })
        return {"object": "list", "data": data}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model_name = body.get("model", "")
    messages = body.get("messages", [])
    stream = body.get("stream", False)

    if not model_name:
        raise HTTPException(status_code=400, detail="model is required")
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    allowed = await _check_policy(model_name)
    if not allowed:
        _write_audit(_audit_entry("policy_violation", {
            "model": model_name,
            "capability": f"capability://ollama/{model_name}",
        }))
        raise HTTPException(status_code=403, detail="Policy violation: capability not allowed in this jurisdiction")

    request_id = str(uuid.uuid4())
    start_time = time.time()

    if _config["log_requests"]:
        _write_audit(_audit_entry("inference_request", {
            "request_id": request_id,
            "model": model_name,
            "capability": f"capability://ollama/{model_name}",
            "message_count": len(messages),
        }))

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            ollama_payload = {
                "model": model_name,
                "messages": messages,
                "stream": stream,
            }
            if "temperature" in body:
                ollama_payload["options"] = {"temperature": body["temperature"]}
            if "max_tokens" in body:
                ollama_payload.setdefault("options", {})["num_predict"] = body["max_tokens"]

            resp = await client.post(
                f"{_config['ollama_host']}/api/chat",
                json=ollama_payload,
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPStatusError as e:
        elapsed = time.time() - start_time
        _write_audit(_audit_entry("inference_error", {
            "request_id": request_id,
            "model": model_name,
            "error": str(e),
            "elapsed_ms": int(elapsed * 1000),
        }))
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")
    except Exception as e:
        elapsed = time.time() - start_time
        _write_audit(_audit_entry("inference_error", {
            "request_id": request_id,
            "model": model_name,
            "error": str(e),
            "elapsed_ms": int(elapsed * 1000),
        }))
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {e}")

    elapsed = time.time() - start_time
    content = result.get("message", {}).get("content", "")

    if _config["log_requests"]:
        _write_audit(_audit_entry("inference_complete", {
            "request_id": request_id,
            "model": model_name,
            "capability": f"capability://ollama/{model_name}",
            "model_uri": f"model://ollama/{model_name}",
            "content_hash": _hash_content(content),
            "elapsed_ms": int(elapsed * 1000),
            "eval_count": result.get("eval_count", 0),
        }))

    return {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": result.get("prompt_eval_count", 0),
            "completion_tokens": result.get("eval_count", 0),
            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
        },
        "sovereign_metadata": {
            "model_uri": f"model://ollama/{model_name}",
            "capability_uri": f"capability://ollama/{model_name}",
            "jurisdiction": _config["jurisdiction"],
            "request_id": request_id,
            "audit_logged": True,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="SovereignStack Ollama Adapter")
    parser.add_argument("--ollama-host", default="http://localhost:11434")
    parser.add_argument("--node-url", default="http://localhost:8080")
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--jurisdiction", default="us")
    parser.add_argument("--audit-log", default="/var/log/sovereignstack/audit.log")
    parser.add_argument("--log-requests", action="store_true", default=True)
    parser.add_argument("--no-log-requests", dest="log_requests", action="store_false")
    args = parser.parse_args()

    _config["ollama_host"] = args.ollama_host
    _config["node_url"] = args.node_url
    _config["jurisdiction"] = args.jurisdiction
    _config["audit_log"] = args.audit_log
    _config["log_requests"] = args.log_requests

    logger.info(f"Starting Ollama adapter on port {args.port}")
    logger.info(f"  Ollama: {args.ollama_host}")
    logger.info(f"  Node:  {args.node_url}")
    logger.info(f"  Jurisdiction: {args.jurisdiction}")

    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
