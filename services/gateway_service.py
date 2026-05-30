from fastapi import FastAPI, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import requests
import uuid
import json
import re
import time
from datetime import datetime, timezone
from collections import defaultdict
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient, InvalidTokenError

from services.spiffe_helper import spiffe_ctx, SPIFFE_TRUST_DOMAIN
from services.graphql_schema import graphql_app
from services.merkle_audit import append_event, get_current_root, get_proof_for_event, get_tree_size, get_merkle_tree

load_dotenv()

import asyncio

async def rate_limit_cleaner():
    while True:
        await asyncio.sleep(600)  # Clean every 10 minutes
        now = time.time()
        expired_ips = [ip for ip, ts_list in request_counts.items() if not ts_list or now - ts_list[-1] >= RATE_LIMIT_WINDOW]
        for ip in expired_ips:
            request_counts.pop(ip, None)

@asynccontextmanager
async def lifespan(app: FastAPI):
    spiffe_ctx.init()
    cleaner_task = asyncio.create_task(rate_limit_cleaner())
    yield
    cleaner_task.cancel()
    spiffe_ctx.close()

app = FastAPI(title="OASA Gateway Service", version="2026.1", lifespan=lifespan)

BACKEND = os.getenv("INFERENCE_BACKEND", "vllm").lower()
COMPUTE_URL = os.getenv("COMPUTE_URL", "http://vllm:8000")
try:
    MODEL_ROUTES = json.loads(os.getenv("MODEL_ROUTES_JSON", "{}"))
except json.JSONDecodeError:
    MODEL_ROUTES = {}
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory:8082")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
AUDIT_PATH = os.path.join(DATA_DIR, "audit.log")
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "http://keycloak:8083/realms/sovereign")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "sovereign-gateway")

jwks_client = PyJWKClient(f"{OIDC_ISSUER_URL}/protocol/openid-connect/certs", cache_keys=True)
_jwks_cache_time = 0.0

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
request_counts = defaultdict(list)

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    oasa_compliance_lock: bool = False
    use_rag: bool = True
    oasa_audit_tag: str | None = None
    oasa_jurisdiction: str | None = None
    temperature: float | None = 0.2
    max_tokens: int | None = 1024
    stream: bool | None = False

def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    request_counts[client_ip] = [ts for ts in request_counts[client_ip] if now - ts < RATE_LIMIT_WINDOW]
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    request_counts[client_ip].append(now)
    return True

def audit(event: dict):
    event["ts"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    append_event(event)

def run_opa_policy_check(prompt: str) -> tuple[bool, str]:
    if re.search(r"\d{3}-\d{2}-\d{4}", prompt):
        return False, "OPA Policy Violation (Rule: DLP-Block-SSN) — Prompt contains sensitive PII"
    if re.search(r"\d{4}-\d{4}-\d{4}-\d{4}", prompt):
        return False, "OPA Policy Violation (Rule: DLP-Block-CreditCard) — Prompt contains credit card details"
    return True, ""

def validate_oidc_jwt(authorization: str | None) -> tuple[bool, dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return False, {}
    token = authorization.split(" ")[1]
    for retry in range(2):
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=OIDC_CLIENT_ID,
                issuer=OIDC_ISSUER_URL,
                options={"verify_exp": True},
            )
            roles = claims.get("realm_access", {}).get("roles", [])
            claims["roles"] = roles
            return True, claims
        except InvalidTokenError:
            break
        except Exception:
            if retry == 0:
                continue
            break
            
    # Mock token validation only if explicitly enabled (for testing)
    if os.getenv("OASA_ALLOW_MOCK_TOKENS", "false").lower() == "true":
        if token == "mock-valid-token":
            return True, {"sub": "user-123", "roles": ["inference:write"]}
        if token == "mock-unauthorized-role":
            return True, {"sub": "user-456", "roles": ["audit:read"]}
        if len(token) > 10 and not token.startswith("ey"):
            return True, {"sub": "generic-user", "roles": ["inference:write"]}
            
    return False, {}

def handle_auth(authorization: str | None, request_id: str, trace_id: str) -> JSONResponse | None:
    is_authenticated, claims = validate_oidc_jwt(authorization)
    if not is_authenticated:
        audit({"type": "auth_failure", "id": request_id, "reason": "Missing or invalid OIDC bearer token", "trace_id": trace_id})
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": {"message": "Unauthorized. A valid Keycloak/OIDC Bearer token is required.", "type": "invalid_auth_error", "code": "401"}})
    roles = claims.get("roles", [])
    if "inference:write" not in roles:
        audit({"type": "rbac_failure", "id": request_id, "reason": f"Required role inference:write missing in user roles: {roles}", "trace_id": trace_id})
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"error": {"message": "Forbidden. User does not possess required inference write permissions.", "type": "rbac_permission_error", "code": "403"}})
    return None

def fetch_rag_context(user_prompt: str) -> str:
    try:
        headers = {}
        if spiffe_ctx.ready:
            auth_h = spiffe_ctx.get_auth_header("memory")
            if auth_h:
                headers.update(auth_h)
        r = requests.post(f"{MEMORY_URL}/query", json={"query": user_prompt}, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("context", "")
    except Exception:
        pass
    return ""

def execute_inference(payload: ChatCompletionRequest, messages: list, user_prompt: str, context: str) -> tuple[bool, str]:
    compute_url = MODEL_ROUTES.get(payload.model, COMPUTE_URL)
    if BACKEND == "vllm":
        vllm_payload = {"model": payload.model, "messages": messages, "temperature": payload.temperature or 0.2, "max_tokens": payload.max_tokens or 1024, "stream": False}
        try:
            r = requests.post(f"{compute_url}/v1/chat/completions", json=vllm_payload, timeout=30)
            if r.status_code == 200:
                return False, r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return True, ""
    else:
        try:
            r = requests.post(f"{compute_url}/completion", json={"model": payload.model, "prompt": user_prompt, "context": context}, timeout=10)
            if r.status_code == 200:
                return False, r.json().get("response", "")
        except Exception:
            pass
        return True, ""

@app.post("/v1/chat/completions")
def chat(payload: ChatCompletionRequest, request: Request, authorization: str | None = Header(None)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error", "code": "429"}})

    request_id = str(uuid.uuid4())
    user_prompt = payload.messages[-1].get("content", "") if payload.messages else ""
    compliance_mode = os.getenv("OASA_ENFORCE_COMPLIANCE", "STRICT")
    auth_enforced = os.getenv("OASA_ENFORCE_AUTH", "STRICT")
    policy_enforced = os.getenv("OASA_ENFORCE_POLICY", "STRICT")
    otel_enabled = os.getenv("OASA_OPENTELEMETRY_ENABLED", "true")
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()).replace("-", ""))
    span_id = request.headers.get("x-span-id", str(uuid.uuid4()).replace("-", "")[:16])

    if auth_enforced == "STRICT":
        auth_error = handle_auth(authorization, request_id, trace_id)
        if auth_error:
            return auth_error

    if policy_enforced == "STRICT":
        policy_passed, policy_error = run_opa_policy_check(user_prompt)
        if not policy_passed:
            audit({"type": "policy_violation", "id": request_id, "reason": policy_error, "trace_id": trace_id})
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"error": {"message": policy_error, "type": "policy_governance_block", "code": "403"}})

    truncated_prompt = user_prompt[:1000] + "... [TRUNCATED]" if len(user_prompt) > 1000 else user_prompt
    audit_payload = {"type": "request", "id": request_id, "model": payload.model, "prompt": truncated_prompt, "oasa_compliance_lock": payload.oasa_compliance_lock, "oasa_audit_tag": payload.oasa_audit_tag, "oasa_jurisdiction": payload.oasa_jurisdiction}
    
    if spiffe_ctx.ready:
        audit_payload["spiffe_id"] = spiffe_ctx.identity
    if otel_enabled == "true":
        audit_payload["trace_id"] = trace_id
        audit_payload["span_id"] = span_id
        
    audit(audit_payload)

    if compliance_mode == "STRICT" and not payload.oasa_compliance_lock:
        audit({"type": "compliance_violation", "id": request_id, "reason": "Missing or false oasa_compliance_lock in STRICT mode", "trace_id": trace_id})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": {"message": "OASA compliance lock is required and must be set to true in STRICT compliance mode.", "type": "invalid_request_error", "code": "400"}})

    context = fetch_rag_context(user_prompt) if payload.use_rag else ""

    messages = list(payload.messages)
    if context:
        messages.insert(0, {"role": "system", "content": f"Relevant context:\n{context[:2000]}"})

    compute_failed, answer = execute_inference(payload, messages, user_prompt, context)

    if compute_failed:
        if payload.oasa_compliance_lock:
            audit({"type": "oasa_lock_enforced", "id": request_id, "reason": "Local compute backend failure. Prevented cloud fallback.", "blocked_fallback": "api.openai.com", "trace_id": trace_id})
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"error": {"message": "Local AI engine failed. OASA-Lock prevented external fallback.", "type": "oasa_lock_enforcement", "code": "503"}})
        else:
            audit({"type": "exfiltration_warning", "id": request_id, "reason": "Local compute failure. Falling back to external cloud API.", "destination": "api.openai.com", "trace_id": trace_id})
            answer = f"[FALLBACK - api.openai.com] Simulated cloud fallback response for prompt: {user_prompt}"

    truncated_answer = answer[:1000] + "... [TRUNCATED]" if len(answer) > 1000 else answer
    res_audit = {"type": "response", "id": request_id, "response": truncated_answer, "oasa_compliance_lock": payload.oasa_compliance_lock, "oasa_audit_tag": payload.oasa_audit_tag, "oasa_jurisdiction": payload.oasa_jurisdiction}
    
    if otel_enabled == "true":
        res_audit["trace_id"] = trace_id
        res_audit["span_id"] = span_id
        
    audit(res_audit)

    return JSONResponse(status_code=status.HTTP_200_OK, content={"id": request_id, "object": "chat.completion", "model": payload.model, "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}}]})

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "spiffe_enabled": spiffe_ctx.ready}

app.include_router(graphql_app, prefix="/graphql")

@app.get("/audit/root")
def audit_root():
    root = get_current_root()
    return {"root": root, "size": get_tree_size()}

@app.get("/audit/proof/{index}")
def audit_proof(index: int):
    try:
        tree = get_merkle_tree()
        event = tree.get_event(index)
        proof = tree.get_proof(index)
        return {"index": index, "event": event, "proof": proof, "root": tree.root}
    except IndexError:
        return JSONResponse(status_code=404, content={"error": f"Event index {index} not found"})

@app.get("/audit/events")
def audit_events(limit: int = 10, offset: int = 0):
    tree = get_merkle_tree()
    events = tree.events[offset:offset + limit]
    return {"events": events, "total": tree.size, "offset": offset, "limit": limit}

@app.get("/.well-known/openid-configuration")
def oidc_config():
    try:
        r = requests.get(f"{OIDC_ISSUER_URL}/.well-known/openid-configuration", timeout=5)
        return JSONResponse(content=r.json())
    except Exception:
        return JSONResponse(content={"issuer": OIDC_ISSUER_URL})

@app.get("/spiffe")
def spiffe_identity():
    if not spiffe_ctx.ready:
        return JSONResponse(content={"spiffe_status": "unavailable", "message": "SPIRE Agent not connected — SPIFFE workload identity unavailable. Ensure SPIFFE_ENABLED=true and SPIRE is running."})
    svid = spiffe_ctx.identity
    return {"spiffe_status": "available", "workload_identity": svid, "trust_domain": SPIFFE_TRUST_DOMAIN}
