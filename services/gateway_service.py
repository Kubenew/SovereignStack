from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, requests, uuid, json
from datetime import datetime, timezone

app = FastAPI(title="OASA Gateway Service", version="2026.1")

COMPUTE_URL = os.getenv("COMPUTE_URL", "http://compute:8083")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory:8082")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
AUDIT_PATH = os.path.join(DATA_DIR, "audit.log")

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    oasa_compliance_lock: bool = False
    use_rag: bool = True
    oasa_audit_tag: str | None = None
    oasa_jurisdiction: str | None = None

def audit(event: dict):
    event["ts"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

@app.post("/v1/chat/completions")
def chat(payload: ChatCompletionRequest):
    request_id = str(uuid.uuid4())
    user_prompt = payload.messages[-1].get("content", "")
    compliance_mode = os.getenv("OASA_ENFORCE_COMPLIANCE", "STRICT")

    # Audit the incoming request details
    audit({
        "type": "request",
        "id": request_id,
        "model": payload.model,
        "prompt": user_prompt,
        "oasa_compliance_lock": payload.oasa_compliance_lock,
        "oasa_audit_tag": payload.oasa_audit_tag,
        "oasa_jurisdiction": payload.oasa_jurisdiction
    })

    # Axiom 1 & Lock Check: Reject requests in STRICT mode if lock is not enabled
    if compliance_mode == "STRICT" and not payload.oasa_compliance_lock:
        audit({
            "type": "compliance_violation",
            "id": request_id,
            "reason": "Missing or false oasa_compliance_lock in STRICT mode"
        })
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": "OASA compliance lock is required and must be set to true in STRICT compliance mode.",
                    "type": "invalid_request_error",
                    "code": "400"
                }
            }
        )

    context = ""
    if payload.use_rag:
        try:
            r = requests.post(f"{MEMORY_URL}/query", json={"query": user_prompt})
            if r.status_code == 200:
                context = r.json().get("context", "")
        except Exception:
            context = ""

    # Call local compute engine
    try:
        r = requests.post(
            f"{COMPUTE_URL}/completion",
            json={"model": payload.model, "prompt": user_prompt, "context": context},
            timeout=10
        )
        compute_failed = (r.status_code != 200)
    except Exception:
        compute_failed = True

    # If local compute fails, handle compliance lock
    if compute_failed:
        if payload.oasa_compliance_lock:
            # Audit the Lock enforcement event
            audit({
                "type": "oasa_lock_enforced",
                "id": request_id,
                "reason": "Local compute backend failure. Prevented cloud fallback.",
                "blocked_fallback": "api.openai.com"
            })
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": {
                        "message": "Local AI engine failed. OASA-Lock prevented external fallback.",
                        "type": "oasa_lock_enforcement",
                        "code": "503"
                    }
                }
            )
        else:
            # Non-strict mode, exfiltrate to external simulated cloud service
            audit({
                "type": "exfiltration_warning",
                "id": request_id,
                "reason": "Local compute failure. Falling back to external cloud API.",
                "destination": "api.openai.com"
            })
            answer = f"[FALLBACK - api.openai.com] Simulated cloud fallback response for prompt: {user_prompt}"
    else:
        answer = r.json().get("response", "")

    # Audit the response
    audit({
        "type": "response",
        "id": request_id,
        "response": answer,
        "oasa_compliance_lock": payload.oasa_compliance_lock,
        "oasa_audit_tag": payload.oasa_audit_tag,
        "oasa_jurisdiction": payload.oasa_jurisdiction
    })

    return {
        "id": request_id,
        "object": "chat.completion",
        "model": payload.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}}]
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

