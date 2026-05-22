from fastapi import FastAPI, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, requests, uuid, json, re
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

# OPA DLP Check Simulation
def run_opa_policy_check(prompt: str) -> tuple[bool, str]:
    """Simulates an OPA Rego policy evaluation for DLP and safety governance."""
    # DLP Rule: Block SSNs
    if re.search(r"\d{3}-\d{2}-\d{4}", prompt):
        return False, "OPA Policy Violation (Rule: DLP-Block-SSN) — Prompt contains sensitive PII"
    # DLP Rule: Block credit cards
    if re.search(r"\d{4}-\d{4}-\d{4}-\d{4}", prompt):
        return False, "OPA Policy Violation (Rule: DLP-Block-CreditCard) — Prompt contains credit card details"
    return True, ""

# JWT Mock Decoder
def validate_oidc_jwt(authorization: str | None) -> tuple[bool, dict]:
    """Simulates validating a Keycloak/OIDC JWT bearer token."""
    if not authorization:
        return False, {}
    if not authorization.startswith("Bearer "):
        return False, {}
    token = authorization.split(" ")[1]
    
    # For testing/mocking, check if it's a valid JSON string or mock string
    try:
        # If token is base64 or JSON-like, parse it
        if token.startswith("{"):
            claims = json.loads(token)
            return True, claims
        elif token == "mock-valid-token":
            return True, {"sub": "user-123", "roles": ["inference:write"]}
        elif token == "mock-unauthorized-role":
            return True, {"sub": "user-456", "roles": ["audit:read"]}
    except Exception:
        pass
    
    # Generic verification for testing
    if len(token) > 10:
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

    # Generate mock OpenTelemetry context
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()).replace("-", ""))
    span_id = request.headers.get("x-span-id", str(uuid.uuid4()).replace("-", "")[:16])

    # 1. Identity & SSO Layer (OIDC) Check
    if auth_enforced == "STRICT":
        is_authenticated, claims = validate_oidc_jwt(authorization)
        if not is_authenticated:
            audit({
                "type": "auth_failure",
                "id": request_id,
                "reason": "Missing or invalid OIDC bearer token",
                "trace_id": trace_id
            })
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "message": "Unauthorized. A valid Keycloak/OIDC Bearer token is required.",
                        "type": "invalid_auth_error",
                        "code": "401"
                    }
                }
            )
        # RBAC Check: Need inference:write scope/role
        roles = claims.get("roles", [])
        if "inference:write" not in roles:
            audit({
                "type": "rbac_failure",
                "id": request_id,
                "reason": f"Required role inference:write missing in user roles: {roles}",
                "trace_id": trace_id
            })
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": {
                        "message": "Forbidden. User does not possess required inference write permissions.",
                        "type": "rbac_permission_error",
                        "code": "403"
                    }
                }
            )

    # 2. OPA Policy Governance & DLP Checks
    if policy_enforced == "STRICT":
        policy_passed, policy_error = run_opa_policy_check(user_prompt)
        if not policy_passed:
            audit({
                "type": "policy_violation",
                "id": request_id,
                "reason": policy_error,
                "trace_id": trace_id
            })
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": {
                        "message": policy_error,
                        "type": "policy_governance_block",
                        "code": "403"
                    }
                }
            )

    # Audit the incoming request details with trace headers
    audit_payload = {
        "type": "request",
        "id": request_id,
        "model": payload.model,
        "prompt": user_prompt,
        "oasa_compliance_lock": payload.oasa_compliance_lock,
        "oasa_audit_tag": payload.oasa_audit_tag,
        "oasa_jurisdiction": payload.oasa_jurisdiction
    }
    if otel_enabled == "true":
        audit_payload["trace_id"] = trace_id
        audit_payload["span_id"] = span_id
    audit(audit_payload)

    # Axiom 1 & Lock Check: Reject requests in STRICT compliance mode if lock is not enabled
    if compliance_mode == "STRICT" and not payload.oasa_compliance_lock:
        audit({
            "type": "compliance_violation",
            "id": request_id,
            "reason": "Missing or false oasa_compliance_lock in STRICT mode",
            "trace_id": trace_id
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
                "blocked_fallback": "api.openai.com",
                "trace_id": trace_id
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
                "destination": "api.openai.com",
                "trace_id": trace_id
            })
            answer = f"[FALLBACK - api.openai.com] Simulated cloud fallback response for prompt: {user_prompt}"
    else:
        answer = r.json().get("response", "")

    # Audit the response
    res_audit = {
        "type": "response",
        "id": request_id,
        "response": answer,
        "oasa_compliance_lock": payload.oasa_compliance_lock,
        "oasa_audit_tag": payload.oasa_audit_tag,
        "oasa_jurisdiction": payload.oasa_jurisdiction
    }
    if otel_enabled == "true":
        res_audit["trace_id"] = trace_id
        res_audit["span_id"] = span_id
    audit(res_audit)

    return {
        "id": request_id,
        "object": "chat.completion",
        "model": payload.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}}]
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}
