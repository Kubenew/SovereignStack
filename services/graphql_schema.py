import strawberry
from typing import Optional
from strawberry.types import Info as StrawberryInfo
import os
import requests
import uuid
import json
import re
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import Header, Request
from strawberry.fastapi import GraphQLRouter

from services.spiffe_helper import spiffe_ctx, SPIFFE_TRUST_DOMAIN

BACKEND = os.getenv("INFERENCE_BACKEND", "vllm").lower()
COMPUTE_URL = os.getenv("COMPUTE_URL", "http://vllm:8000")
MEMORY_URL = os.getenv("MEMORY_URL", "http://memory:8082")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
AUDIT_PATH = os.path.join(DATA_DIR, "audit.log")
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "http://keycloak:8083/realms/sovereign")

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
request_counts = defaultdict(list)

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

def check_rate_limit(client_ip: str) -> bool:
    import time
    now = time.time()
    request_counts[client_ip] = [ts for ts in request_counts[client_ip] if now - ts < RATE_LIMIT_WINDOW]
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    request_counts[client_ip].append(now)
    return True

def _base_inference_logic(messages_data, model, oasa_compliance_lock, use_rag, oasa_audit_tag,
                          oasa_jurisdiction, temperature, max_tokens, authorization, client_ip, trace_id, span_id):
    request_id = str(uuid.uuid4())
    user_prompt = messages_data[-1].get("content", "") if messages_data else ""
    compliance_mode = os.getenv("OASA_ENFORCE_COMPLIANCE", "STRICT")
    auth_enforced = os.getenv("OASA_ENFORCE_AUTH", "STRICT")
    policy_enforced = os.getenv("OASA_ENFORCE_POLICY", "STRICT")
    otel_enabled = os.getenv("OASA_OPENTELEMETRY_ENABLED", "true")

    if not check_rate_limit(client_ip):
        return {"error": True, "status_code": 429, "message": "Rate limit exceeded"}

    if auth_enforced == "STRICT":
        from services.gateway_service import validate_oidc_jwt
        is_authenticated, claims = validate_oidc_jwt(authorization)
        if not is_authenticated:
            audit({"type": "auth_failure", "id": request_id, "reason": "Missing or invalid OIDC bearer token", "trace_id": trace_id})
            return {"error": True, "status_code": 401, "message": "Unauthorized. A valid Keycloak/OIDC Bearer token is required."}
        roles = claims.get("roles", [])
        if "inference:write" not in roles:
            audit({"type": "rbac_failure", "id": request_id, "reason": f"Required role inference:write missing in user roles: {roles}", "trace_id": trace_id})
            return {"error": True, "status_code": 403, "message": "Forbidden. User does not possess required inference write permissions."}

    if policy_enforced == "STRICT":
        policy_passed, policy_error = run_opa_policy_check(user_prompt)
        if not policy_passed:
            audit({"type": "policy_violation", "id": request_id, "reason": policy_error, "trace_id": trace_id})
            return {"error": True, "status_code": 403, "message": policy_error}

    truncated_prompt = user_prompt[:1000] + "... [TRUNCATED]" if len(user_prompt) > 1000 else user_prompt
    audit_payload = {"type": "request", "id": request_id, "model": model, "prompt": truncated_prompt,
                     "oasa_compliance_lock": oasa_compliance_lock, "oasa_audit_tag": oasa_audit_tag,
                     "oasa_jurisdiction": oasa_jurisdiction, "source": "graphql"}
    if spiffe_ctx.ready:
        audit_payload["spiffe_id"] = spiffe_ctx.identity
    if otel_enabled == "true":
        audit_payload["trace_id"] = trace_id
        audit_payload["span_id"] = span_id
    audit(audit_payload)

    if compliance_mode == "STRICT" and not oasa_compliance_lock:
        audit({"type": "compliance_violation", "id": request_id,
               "reason": "Missing or false oasa_compliance_lock in STRICT mode", "trace_id": trace_id})
        return {"error": True, "status_code": 400, "message": "OASA compliance lock is required in STRICT compliance mode."}

    context = ""
    if use_rag:
        try:
            headers = {}
            if spiffe_ctx.ready:
                auth_h = spiffe_ctx.get_auth_header("memory")
                if auth_h:
                    headers.update(auth_h)
            r = requests.post(f"{MEMORY_URL}/query", json={"query": user_prompt}, headers=headers, timeout=5)
            if r.status_code == 200:
                context = r.json().get("context", "")
        except Exception:
            pass

    messages = list(messages_data)
    if context:
        messages.insert(0, {"role": "system", "content": f"Relevant context:\n{context[:2000]}"})

    compute_failed = False
    answer = ""
    if BACKEND == "vllm":
        vllm_payload = {"model": model, "messages": messages, "temperature": temperature or 0.2,
                        "max_tokens": max_tokens or 1024, "stream": False}
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
            r = requests.post(f"{COMPUTE_URL}/completion", json={"model": model, "prompt": user_prompt, "context": context}, timeout=10)
            compute_failed = (r.status_code != 200)
            if not compute_failed:
                answer = r.json().get("response", "")
        except Exception:
            compute_failed = True

    if compute_failed:
        if oasa_compliance_lock:
            audit({"type": "oasa_lock_enforced", "id": request_id,
                   "reason": "Local compute backend failure. Prevented cloud fallback.",
                   "blocked_fallback": "api.openai.com", "trace_id": trace_id})
            return {"error": True, "status_code": 503, "message": "Local AI engine failed. OASA-Lock prevented external fallback."}
        else:
            audit({"type": "exfiltration_warning", "id": request_id,
                   "reason": "Local compute failure. Falling back to external cloud API.",
                   "destination": "api.openai.com", "trace_id": trace_id})
            answer = f"[FALLBACK - api.openai.com] Simulated cloud fallback response for prompt: {user_prompt}"

    truncated_answer = answer[:1000] + "... [TRUNCATED]" if len(answer) > 1000 else answer
    res_audit = {"type": "response", "id": request_id, "response": truncated_answer,
                 "oasa_compliance_lock": oasa_compliance_lock, "oasa_audit_tag": oasa_audit_tag,
                 "oasa_jurisdiction": oasa_jurisdiction}
    if otel_enabled == "true":
        res_audit["trace_id"] = trace_id
        res_audit["span_id"] = span_id
    audit(res_audit)

    return {"error": False, "id": request_id, "model": model, "content": answer}


@strawberry.type
class HealthStatus:
    status: str
    service: str
    spiffe_enabled: bool

@strawberry.type
class SpiffeIdentity:
    spiffe_status: str
    workload_identity: Optional[str] = None
    trust_domain: Optional[str] = None

@strawberry.type
class OIDCConfig:
    issuer: Optional[str] = None

@strawberry.type
class Message:
    role: str
    content: str

@strawberry.type
class Choice:
    index: int
    message: Message

@strawberry.type
class ChatCompletionPayload:
    id: str
    object: str
    model: str
    choices: list[Choice]

@strawberry.type
class MutationResult:
    success: bool
    payload: Optional[ChatCompletionPayload] = None
    error: Optional[str] = None

@strawberry.input
class MessageInput:
    role: str
    content: str

@strawberry.input
class ChatCompletionInput:
    model: str
    messages: list[MessageInput]
    oasa_compliance_lock: bool = False
    use_rag: bool = True
    oasa_audit_tag: Optional[str] = None
    oasa_jurisdiction: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1024


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> HealthStatus:
        return HealthStatus(status="ok", service="gateway", spiffe_enabled=spiffe_ctx.ready)

    @strawberry.field
    def spiffe_identity(self) -> SpiffeIdentity:
        if not spiffe_ctx.ready:
            return SpiffeIdentity(
                spiffe_status="unavailable",
                workload_identity=None,
                trust_domain=None,
            )
        return SpiffeIdentity(
            spiffe_status="available",
            workload_identity=spiffe_ctx.identity,
            trust_domain=SPIFFE_TRUST_DOMAIN,
        )

    @strawberry.field
    def oidc_config(self) -> OIDCConfig:
        try:
            r = requests.get(f"{OIDC_ISSUER_URL}/.well-known/openid-configuration", timeout=5)
            data = r.json()
            return OIDCConfig(issuer=data.get("issuer"))
        except Exception:
            return OIDCConfig(issuer=OIDC_ISSUER_URL)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def chat_completion(self, input: ChatCompletionInput, info: StrawberryInfo) -> MutationResult:
        request = info.context["request"]
        authorization = request.headers.get("authorization")
        x_trace_id = request.headers.get("x-trace-id")
        x_span_id = request.headers.get("x-span-id")
        client_ip = request.client.host if request.client else "graphql"
        trace_id = x_trace_id or str(uuid.uuid4()).replace("-", "")
        span_id = x_span_id or str(uuid.uuid4()).replace("-", "")[:16]
        messages_data = [{"role": m.role, "content": m.content} for m in input.messages]
        result = _base_inference_logic(
            messages_data=messages_data,
            model=input.model,
            oasa_compliance_lock=input.oasa_compliance_lock,
            use_rag=input.use_rag,
            oasa_audit_tag=input.oasa_audit_tag,
            oasa_jurisdiction=input.oasa_jurisdiction,
            temperature=input.temperature,
            max_tokens=input.max_tokens,
            authorization=authorization,
            client_ip=client_ip,
            trace_id=trace_id,
            span_id=span_id,
        )
        if result.get("error"):
            return MutationResult(success=False, error=result["message"])
        payload = ChatCompletionPayload(
            id=result["id"],
            object="chat.completion",
            model=result["model"],
            choices=[Choice(index=0, message=Message(role="assistant", content=result["content"]))],
        )
        return MutationResult(success=True, payload=payload)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
