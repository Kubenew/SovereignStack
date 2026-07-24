"""
vLLM Adapter for SovereignStack

Bridges vLLM's high-throughput inference server into the SovereignStack identity and governance model.
Designed for production GPU clusters running frontier models.

Usage:
    python adapter.py --vllm-host http://localhost:8000 --node-url http://localhost:8080
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
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("vllm-adapter")

app = FastAPI(title="SovereignStack vLLM Adapter", version="0.4.0")

_config = {
    "vllm_host": "http://localhost:8000",
    "node_url": "http://localhost:8080",
    "jurisdiction": "us",
    "audit_log": "/var/log/sovereignstack/audit.log",
    "max_tokens": 4096,
    "enforce_usage": True,
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
        resp = await client.get(f"{_config['vllm_host']}/v1/models")
        resp.raise_for_status()
        return resp.json().get("data", [])


async def _check_policy(model_name: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{_config['node_url']}/policy/check",
                params={"capability": f"capability://vllm/{model_name}",
                        "jurisdiction": _config["jurisdiction"]},
            )
            if resp.status_code == 200:
                return resp.json().get("allowed", True)
    except Exception:
        pass
    return True


@app.on_event("startup")
async def startup():
    logger.info("Discovering vLLM models...")
    try:
        models = await _discover_models()
        for m in models:
            model_id = m.get("id", "unknown")
            _model_cache[model_id] = {
                "uri": f"model://vllm/{model_id}",
                "capability": f"capability://vllm/{model_id}",
                "owned_by": m.get("owned_by", "vllm"),
            }
            logger.info(f"  Registered: model://vllm/{model_id}")
    except Exception as e:
        logger.warning(f"Could not discover models at startup: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "adapter": "vllm", "models": len(_model_cache)}


@app.get("/v1/models")
async def list_models():
    try:
        models = await _discover_models()
        data = []
        for m in models:
            model_id = m.get("id", "unknown")
            data.append({
                "id": f"vllm/{model_id}",
                "object": "model",
                "created": int(time.time()),
                "owned_by": m.get("owned_by", "vllm"),
                "capabilities_uri": f"capability://vllm/{model_id}",
                "model_uri": f"model://vllm/{model_id}",
            })
        return {"object": "list", "data": data}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"vLLM unreachable: {e}")


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
            "capability": f"capability://vllm/{model_name}",
        }))
        raise HTTPException(status_code=403, detail="Policy violation: capability not allowed in this jurisdiction")

    request_id = str(uuid.uuid4())
    start_time = time.time()

    _write_audit(_audit_entry("inference_request", {
        "request_id": request_id,
        "model": model_name,
        "capability": f"capability://vllm/{model_name}",
        "message_count": len(messages),
        "stream": stream,
    }))

    try:
        async with httpx.AsyncClient(timeout=600) as client:
            vllm_payload = {
                "model": model_name,
                "messages": messages,
                "stream": stream,
            }
            if "temperature" in body:
                vllm_payload["temperature"] = body["temperature"]
            if "max_tokens" in body:
                vllm_payload["max_tokens"] = body["max_tokens"]
            else:
                vllm_payload["max_tokens"] = _config["max_tokens"]
            if "tools" in body:
                vllm_payload["tools"] = body["tools"]

            resp = await client.post(
                f"{_config['vllm_host']}/v1/chat/completions",
                json=vllm_payload,
            )
            resp.raise_for_status()

            if stream:
                async def stream_with_audit():
                    full_content = ""
                    async for chunk in resp.aiter_bytes():
                        yield chunk
                    elapsed = time.time() - start_time
                    _write_audit(_audit_entry("inference_complete", {
                        "request_id": request_id,
                        "model": model_name,
                        "capability": f"capability://vllm/{model_name}",
                        "model_uri": f"model://vllm/{model_name}",
                        "elapsed_ms": int(elapsed * 1000),
                        "stream": True,
                    }))

                return StreamingResponse(
                    stream_with_audit(),
                    media_type="text/event-stream",
                    headers={"X-Sovereign-Request-Id": request_id},
                )

            result = resp.json()
    except httpx.HTTPStatusError as e:
        elapsed = time.time() - start_time
        _write_audit(_audit_entry("inference_error", {
            "request_id": request_id,
            "model": model_name,
            "error": str(e),
            "elapsed_ms": int(elapsed * 1000),
        }))
        raise HTTPException(status_code=502, detail=f"vLLM error: {e}")
    except Exception as e:
        elapsed = time.time() - start_time
        _write_audit(_audit_entry("inference_error", {
            "request_id": request_id,
            "model": model_name,
            "error": str(e),
            "elapsed_ms": int(elapsed * 1000),
        }))
        raise HTTPException(status_code=502, detail=f"vLLM unreachable: {e}")

    elapsed = time.time() - start_time
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = result.get("usage", {})

    _write_audit(_audit_entry("inference_complete", {
        "request_id": request_id,
        "model": model_name,
        "capability": f"capability://vllm/{model_name}",
        "model_uri": f"model://vllm/{model_name}",
        "content_hash": _hash_content(content),
        "elapsed_ms": int(elapsed * 1000),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }))

    result["sovereign_metadata"] = {
        "model_uri": f"model://vllm/{model_name}",
        "capability_uri": f"capability://vllm/{model_name}",
        "jurisdiction": _config["jurisdiction"],
        "request_id": request_id,
        "audit_logged": True,
    }

    return result


@app.post("/v1/completions")
async def completions(request: Request):
    body = await request.json()
    model_name = body.get("model", "")
    prompt = body.get("prompt", "")

    if not model_name:
        raise HTTPException(status_code=400, detail="model is required")

    allowed = await _check_policy(model_name)
    if not allowed:
        raise HTTPException(status_code=403, detail="Policy violation")

    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=600) as client:
            resp = await client.post(
                f"{_config['vllm_host']}/v1/completions",
                json={"model": model_name, "prompt": prompt,
                       "max_tokens": body.get("max_tokens", _config["max_tokens"])},
            )
            resp.raise_for_status()
            result = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"vLLM error: {e}")

    elapsed = time.time() - start_time

    _write_audit(_audit_entry("inference_complete", {
        "request_id": request_id,
        "model": model_name,
        "capability": f"capability://vllm/{model_name}",
        "elapsed_ms": int(elapsed * 1000),
        "type": "completion",
    }))

    result["sovereign_metadata"] = {
        "model_uri": f"model://vllm/{model_name}",
        "capability_uri": f"capability://vllm/{model_name}",
        "jurisdiction": _config["jurisdiction"],
        "request_id": request_id,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="SovereignStack vLLM Adapter")
    parser.add_argument("--vllm-host", default="http://localhost:8000")
    parser.add_argument("--node-url", default="http://localhost:8080")
    parser.add_argument("--port", type=int, default=9200)
    parser.add_argument("--jurisdiction", default="us")
    parser.add_argument("--audit-log", default="/var/log/sovereignstack/audit.log")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--enforce-usage", action="store_true", default=True)
    args = parser.parse_args()

    _config["vllm_host"] = args.vllm_host
    _config["node_url"] = args.node_url
    _config["jurisdiction"] = args.jurisdiction
    _config["audit_log"] = args.audit_log
    _config["max_tokens"] = args.max_tokens
    _config["enforce_usage"] = args.enforce_usage

    logger.info(f"Starting vLLM adapter on port {args.port}")
    logger.info(f"  vLLM:  {args.vllm_host}")
    logger.info(f"  Node:  {args.node_url}")
    logger.info(f"  Jurisdiction: {args.jurisdiction}")

    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
