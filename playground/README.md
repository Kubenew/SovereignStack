# Sovereign Playground

Deploy a full OASA-compliant AI stack on your laptop in **2 minutes**.

## Prerequisites

- Docker Desktop with **GPU support** (NVIDIA Container Toolkit)
- At least **16 GB RAM** (32 GB recommended)
- A GGUF model file (e.g., download from HuggingFace)

## Quick Start

### 1. Download a Model

```bash
# Example: Mistral-7B-Instruct (INT4, ~4GB)
mkdir -p playground/models
cd playground/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  -O model.gguf
```

### 2. Start the Stack

```bash
cd playground/
docker compose up -d
```

Wait ~60 seconds for the model to load, then check:

```bash
docker compose logs -f inference
# Look for: "server is listening on 0.0.0.0:8000"
```

### 3. Send Your First Request

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "playground-model",
    "messages": [{"role": "user", "content": "What is GDPR?"}],
    "oasa_compliance_lock": true
  }'
```

### 4. Verify Air-Gap Isolation

```bash
# From your host machine
python ../tools/sovereign_stack.py audit-network
```

## What's Running?

| Service | Port | Description |
|---|---|---|
| **Gateway** | `8080` | OpenAI-compatible API proxy with OASA-Lock |
| **Inference** | `8000` | llama.cpp server running your GGUF model |
| **Vector DB** | `6333` | Qdrant vector store (encrypted at rest) |
| **Dashboard** | `3000` | Compliance monitoring UI |

## Architecture

```
Your App (curl / Python / LangChain)
         │
         ▼
  ┌──────────────┐
  │   Gateway    │ :8080  — OASA-Lock enforced
  │ turboprivate │        — Blocks external API fallback
  └──────┬───────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Inference│ │VectorDB│
│llama.cpp│ │ Qdrant │
│  :8000  │ │ :6333  │
└─────────┘ └────────┘
```

> **Note:** The Docker network is set to `internal: true`.
> No container can reach the internet. This enforces OASA Axiom 1 at the network level.

## Stop

```bash
docker compose down
# To also remove data:
docker compose down -v
```

## CPU-Only Mode

If you don't have an NVIDIA GPU, remove the `deploy.resources` section from `docker-compose.yml` and use a smaller model:

```bash
# Phi-3-mini (3.8B, ~2.3GB)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf \
  -O models/model.gguf
```
