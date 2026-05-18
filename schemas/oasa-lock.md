# OASA-Lock: The Compliance Poison Pill

## Purpose

The **OASA-Lock** is a mandatory enforcement mechanism designed to prevent accidental or malicious data exfiltration from a Sovereign Node. It acts as a "poison pill" for inference routing.

In standard enterprise environments, API gateways are often configured with failover routing. If a local model fails (due to Out Of Memory, crashes, or timeouts), the gateway might fall back to a public cloud API (e.g., OpenAI, Anthropic).

**For Sovereign AI, fallback is catastrophic.** Sending confidential enterprise data, Protected Health Information (PHI), or unreleased financial reports to a third-party cloud API immediately violates GDPR, HIPAA, and corporate data governance policies, potentially resulting in massive fines.

OASA-Lock guarantees the safe failure mode: **Fail Closed**.

## Mechanism

### 1. The Request Flag
Every request to the `/v1/chat/completions` or `/v1/embeddings` endpoint must include the `oasa_compliance_lock` flag set to `true`.

```json
{
  "model": "sovereign-llama3-70b-turboquant",
  "messages": [{"role": "user", "content": "Analyze confidential audit report."}],
  "oasa_compliance_lock": true
}
```

The OASA request schema explicitly requires this field. If it is missing or set to `false`, the gateway **must** reject the request with `400 Bad Request` in `STRICT` compliance mode.

### 2. The Enforcement Action
When the gateway processes a request with `oasa_compliance_lock: true`, it binds the request strictly to local execution.

If the local AI engine (`TurboQuant` / `llama.cpp` / `vLLM`) fails to serve the request, the gateway is strictly prohibited from routing the request to any external API.

Instead, the gateway must return:
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "error": {
    "message": "Local AI engine failed. OASA-Lock prevented external fallback.",
    "type": "oasa_lock_enforcement",
    "code": "503"
  }
}
```

### 3. Active Network Blocking
To provide defense-in-depth, the `turboprivate-ai` gateway actively blocks DNS resolution and network connections to known external AI APIs:
- `api.openai.com`
- `api.anthropic.com`
- `generativelanguage.googleapis.com`
- `api.cohere.ai`

This ensures that even if application logic is bypassed, the network layer prevents exfiltration.

## Configuration

In `sovereign-stack.yaml`, the OASA-Lock is configured under the `api` section:

```yaml
api:
  oasa_lock:
    enabled: true
    on_local_failure: "BLOCK"       # BLOCK (503) | QUEUE | DEGRADE
    block_external_apis:
      - "api.openai.com"
      - "api.anthropic.com"
    audit_blocked_attempts: true
```

## Auditing
Every time the OASA-Lock prevents an external fallback, an entry must be written to the immutable audit log (`/var/log/oasa/audit.jsonl`). This allows compliance officers to demonstrate that the system successfully contained the data during a failure event.
