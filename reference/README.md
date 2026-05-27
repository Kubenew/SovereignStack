# Sovereign Minimal Node Reference

This directory contains a **reference implementation** of a minimal sovereign node — the smallest deployable unit of SovereignStack infrastructure.

---

## What is a Minimal Sovereign Node?

A minimal node provides:

- **Local AI inference** — chat completions via an OpenAI-compatible API
- **Encrypted memory** — vector store with AES-256-GCM at rest
- **Identity** — OIDC authentication via Keycloak
- **Policy enforcement** — OPA DLP and RBAC
- **Audit logging** — immutable append-only log
- **Air-gapped operation** — zero WAN egress by default

---

## Contents

| File | Purpose |
|---|---|
| [docker-compose.yml](docker-compose.yml) | Single-node Docker Compose stack |
| [sovereign-stack.yaml](sovereign-stack.yaml) | OASA 2026.1 node manifest |
| [.env.example](.env.example) | Environment configuration template |

---

## Quick Start

```bash
# 1. Clone and enter reference directory
cd reference

# 2. Copy environment config
cp .env.example .env

# 3. Start the node
docker compose up --build -d

# 4. Verify health
curl http://localhost:8080/health

# 5. Send a chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-valid-token" \
  -d '{
    "model":"Qwen/Qwen2.5-7B-Instruct",
    "messages":[{"role":"user","content":"Hello"}],
    "oasa_compliance_lock":true
  }'
```

---

## Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 32 GB |
| GPU | None (CPU OK) | RTX 3090 / A100 |
| Disk | 10 GB | 50 GB |
| Docker | 24+ | 27+ |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     sovereign-isolated-net               │
│                     driver: bridge, internal: true       │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Keycloak │  │ Gateway  │  │ vLLM     │  │ Memory   │ │
│  │ :8083    │←→│ :8080    │←→│ :8000    │  │ :8082    │ │
│  └──────────┘  └────┬─────┘  └──────────┘  └──────────┘ │
│                     │                                     │
│              ┌──────▼──────┐                              │
│              │   Ingest    │                              │
│              │   :8081     │                              │
│              └─────────────┘                              │
└─────────────────────────────────────────────────────────┘
```

---

## Configuration

### Sovereign Stack Manifest

See [sovereign-stack.yaml](sovereign-stack.yaml) for the full OASA 2026.1 node manifest.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `legacy` |
| `VLLM_MODEL_NAME` | `Qwen/Qwen2.5-7B-Instruct` | Inference model |
| `VLLM_GPU_MEMORY_UTIL` | `0.90` | GPU utilization |
| `VLLM_MAX_MODEL_LEN` | `4096` | Max context length |
| `OASA_ENFORCE_AUTH` | `STRICT` | Auth mode |
| `OASA_ENFORCE_COMPLIANCE` | `STRICT` | Compliance mode |

---

## Testing Conformance

```bash
# Run conformance tests against this node
python -m pytest tests/conformance/ -v --level L2
```

---

## Next Steps

- Add more nodes: see [Federation Mesh](/docs/networking/index.md)
- Deploy to production: see [Helm Chart](/deploy/docker-compose.prod.yml)
- Customize profiles: see [Deployment Profiles](/docs/deployment/profiles.md)
