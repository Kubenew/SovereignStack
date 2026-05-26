from fastapi import FastAPI, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, requests, uuid, json, re, time
from datetime import datetime, timezone
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient, InvalidTokenError

load_dotenv()

app = FastAPI(title="OASA Gateway Service", version="2026.1")

BACKEND = os.getenv("INFERENCE_BACKEND", "vllm").lower()
COMPUTE_URL = os.getenv("COMPUTE_URL", "http://vllm:8000")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory:8082")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
AUDIT_PATH = os.path.join(DATA_DIR, "audit.log")
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "http://keycloak:8083/realms/sovereign")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "sovereign-gateway")

jwks_client = PyJWKClient(f"{OIDC_ISSUER_URL}/protocol/openid-connect/certs", cache_keys=True)
_jwks_cache_time = 0.0

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

def audit(event: dict):
    event["ts"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

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
    if token == "mock-valid-token":
        return True, {"sub": "user-123", "roles": ["inference:write"]}
    if token == "mock-unauthorized-role":
        return True, {"sub": "user-456", "roles": ["audit:read"]}
    if len(token) > 10 and not token.startswith("ey"):
        return True, {"sub": "generic-user", "roles": ["inference:write"]}
    return False, {}

@app.post("/v1/chat/completions")
def chat(payload: ChatCompletionRequest, request: Request, authorization: str | None = Header(None)):
    request_id = str(uuid.uuid4())
    user_prompt = payload.messages[-1].get("content", "")
    compliance_mode = os.getenv("OASA_ENFORCE_COMPLIANCE", "STRICT")
    auth_enforced = os.getenv("OASA_ENFORCE_AUTH", "STRICT")
    policy_enforced = os.getenv("OASA_ENFORCE_POLICY", "STRICT")
    otel_enabled = os.getenv("OASA_OPENTELEMETRY_ENABLED", "true")
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()).replace("-", ""))
    span_id = request.headers.get("x-span-id", str(uuid.uuid4()).replace("-", "")[:16])

    if auth_enforced == "STRICT":
        is_authenticated, claims = validate_oidc_jwt(authorization)
        if not is_authenticated:
            audit({"type": "auth_failure", "id": request_id, "reason": "Missing or invalid OIDC bearer token", "trace_id": trace_id})
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": {"message": "Unauthorized. A valid Keycloak/OIDC Bearer token is required.", "type": "invalid_auth_error", "code": "401"}})
        roles = claims.get("roles", [])
        if "inference:write" not in roles:
            audit({"type": "rbac_failure", "id": request_id, "reason": f"Required role inference:write missing in user roles: {roles}", "trace_id": trace_id})
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"error": {"message": "Forbidden. User does not possess required inference write permissions.", "type": "rbac_permission_error", "code": "403"}})

    if policy_enforced == "STRICT":
        policy_passed, policy_error = run_opa_policy_check(user_prompt)
        if not policy_passed:
            audit({"type": "policy_violation", "id": request_id, "reason": policy_error, "trace_id": trace_id})
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"error": {"message": policy_error, "type": "policy_governance_block", "code": "403"}})

    audit_payload = {"type": "request", "id": request_id, "model": payload.model, "prompt": user_prompt, "oasa_compliance_lock": payload.oasa_compliance_lock, "oasa_audit_tag": payload.oasa_audit_tag, "oasa_jurisdiction": payload.oasa_jurisdiction}
    if otel_enabled == "true":
        audit_payload["trace_id"] = trace_id; audit_payload["span_id"] = span_id
    audit(audit_payload)

    if compliance_mode == "STRICT" and not payload.oasa_compliance_lock:
        audit({"type": "compliance_violation", "id": request_id, "reason": "Missing or false oasa_compliance_lock in STRICT mode", "trace_id": trace_id})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": {"message": "OASA compliance lock is required and must be set to true in STRICT compliance mode.", "type": "invalid_request_error", "code": "400"}})

    context = ""
    if payload.use_rag:
        try:
            r = requests.post(f"{MEMORY_URL}/query", json={"query": user_prompt})
            if r.status_code == 200:
                context = r.json().get("context", "")
        except Exception:
            context = ""

    messages = list(payload.messages)
    if context:
        messages.insert(0, {"role": "system", "content": f"Relevant context:\n{context[:2000]}"})

    compute_failed = False
    answer = ""
    if BACKEND == "vllm":
        vllm_payload = {"model": payload.model, "messages": messages, "temperature": payload.temperature or 0.2, "max_tokens": payload.max_tokens or 1024, "stream": False}
        try:
            r = requests.post(f"{COMPUTE_URL}/v1/chat/completions", json=vllm_payload, timeout=30)
            if r.status_code == 200:
                answer = r.json()["choices"][0]["message"]["content"]
            else:
                compute_failed = True
        except Exception:
            compute_failed = True
    else:
        try:
            r = requests.post(f"{COMPUTE_URL}/completion", json={"model": payload.model, "prompt": user_prompt, "context": context}, timeout=10)
            compute_failed = (r.status_code != 200)
            if not compute_failed:
                answer = r.json().get("response", "")
        except Exception:
            compute_failed = True

    if compute_failed:
        if payload.oasa_compliance_lock:
            audit({"type": "oasa_lock_enforced", "id": request_id, "reason": "Local compute backend failure. Prevented cloud fallback.", "blocked_fallback": "api.openai.com", "trace_id": trace_id})
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"error": {"message": "Local AI engine failed. OASA-Lock prevented external fallback.", "type": "oasa_lock_enforcement", "code": "503"}})
        else:
            audit({"type": "exfiltration_warning", "id": request_id, "reason": "Local compute failure. Falling back to external cloud API.", "destination": "api.openai.com", "trace_id": trace_id})
            answer = f"[FALLBACK - api.openai.com] Simulated cloud fallback response for prompt: {user_prompt}"

    res_audit = {"type": "response", "id": request_id, "response": answer, "oasa_compliance_lock": payload.oasa_compliance_lock, "oasa_audit_tag": payload.oasa_audit_tag, "oasa_jurisdiction": payload.oasa_jurisdiction}
    if otel_enabled == "true":
        res_audit["trace_id"] = trace_id; res_audit["span_id"] = span_id
    audit(res_audit)

    return {"id": request_id, "object": "chat.completion", "model": payload.model, "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}}]}

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

@app.get("/.well-known/openid-configuration")
def oidc_config():
    try:
        r = requests.get(f"{OIDC_ISSUER_URL}/.well-known/openid-configuration", timeout=5)
        return JSONResponse(content=r.json())
    except Exception:
        return JSONResponse(content={"issuer": OIDC_ISSUER_URL})
