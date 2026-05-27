# Docker Compose Deployment

For local, personal, and edge deployments. The Docker Compose stack includes all core services on an isolated network.

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
│                                                         │
│  ┌──────────┐  ┌──────────────────┐                     │
│  │ OTEL     │  │ Prometheus       │                     │
│  │ :4317    │  │ :9090            │                     │
│  └──────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Start all services
docker compose up --build -d

# 2. Wait for healthy
docker compose ps

# 3. Check gateway health
curl http://localhost:8080/health

# 4. Send a chat completion
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

## Services

| Service | Image | Port | Depends On | Health Check |
|---|---|---|---|---|
| Keycloak | `keycloak:26.1` | 8083 | — | `/realms/master` |
| Gateway | local build | 8080 | vLLM, Memory, Keycloak | `/health` |
| vLLM | `vllm-openai:v0.7.2` | 8000 | — | `/health` |
| Ingest | local build | 8081 | — | `/health` |
| Memory | local build | 8082 | — | `/health` |
| OTEL Collector | `opentelemetry-collector-contrib:0.122.0` | 4317 | — | — |
| Prometheus | `prometheus:v3.3.0` | 9090 | — | — |

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|---|---|---|
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `legacy` |
| `VLLM_MODEL_NAME` | `Qwen/Qwen2.5-7B-Instruct` | Model for vLLM |
| `VLLM_GPU_MEMORY_UTIL` | `0.90` | GPU memory utilization |
| `VLLM_MAX_MODEL_LEN` | `4096` | Max context length |
| `OASA_ENFORCE_AUTH` | `STRICT` | `STRICT` or `DEVELOPMENT` |
| `OASA_ENFORCE_COMPLIANCE` | `STRICT` | `STRICT` or `DEVELOPMENT` |
| `OASA_ENFORCE_POLICY` | `STRICT` | `STRICT` or `DEVELOPMENT` |

---

## GPU Support

### NVIDIA

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### Apple Silicon

No additional setup required. vLLM does not support macOS; use legacy backend:

```bash
INFERENCE_BACKEND=legacy docker compose up --build -d
```

---

## Air-Gapped Mode

```bash
# Pre-download model weights
docker run --rm -v ./models:/data vllm/vllm-openai:v0.7.2 \
  python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct', local_dir='/data')"

# Set air-gapped env
export HF_HUB_OFFLINE=1

# Start stack (no internet access needed)
docker compose up --build -d
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Gateway 401 | Missing/invalid token | Use `Authorization: Bearer mock-valid-token` or get a real token from Keycloak |
| Gateway 503 | vLLM not ready | Wait for vLLM health check to pass: `docker compose logs -f vllm` |
| OOM on GPU | Context too large | Reduce `VLLM_MAX_MODEL_LEN` or `VLLM_GPU_MEMORY_UTIL` |
| No GPU available | NVIDIA runtime not installed | Run `docker info | grep Runtimes` — should show `nvidia` |
