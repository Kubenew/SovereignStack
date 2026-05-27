# SovereignStack Deployment

This section covers all supported deployment models, from a single laptop to air-gapped datacenter clusters.

---

## Deployment Profiles

| Profile | Target | Resources | Network |
|---|---|---|---|
| [Personal](profiles.md#personal) | Laptop, workstation | 8-32 GB RAM, CPU/1 GPU | Internet (optional) |
| [Edge](profiles.md#edge) | ARM, IoT, low-power | 4-16 GB RAM, CPU | Disconnected |
| [Air-Gapped](profiles.md#air-gapped) | Isolated networks | 16-64 GB RAM, GPU | No WAN egress |
| [Datacenter](profiles.md#datacenter) | GPU clusters | 64+ GB RAM, multi-GPU | Internal fabric |

---

## Deployment Methods

| Method | Profile | Guide |
|---|---|---|
| Docker Compose | Personal, Edge | [Docker Compose Guide](docker-compose.md) |
| Kubernetes / Helm | Air-Gapped, Datacenter | [Helm Guide](helm.md) |

---

## Prerequisites

**All profiles:**
- Docker 24+ or compatible container runtime
- Python 3.10–3.12
- 10 GB free disk (minimum)

**GPU-accelerated profiles:**
- NVIDIA Container Toolkit (Linux)
- NVIDIA driver 535+ (CUDA 12.2)

**Air-gapped profiles:**
- Local container registry mirror (optional but recommended)
- Model weights pre-downloaded and verified

---

## Quick Start

```bash
# 1. Install
curl -sSL https://install.sovereignstack.ai | bash

# 2. Download model
curl -Lo playground/models/model.gguf \
  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# 3. Launch
docker compose up --build -d

# 4. Verify
curl http://localhost:8080/health
```

---

## Architecture Decision Records

For significant deployment architecture decisions, see [RFCs](/rfcs/).
