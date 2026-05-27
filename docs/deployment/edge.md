# Edge Cluster Deployment (K3s + ARM)

Deploy SovereignStack on ARM edge hardware (Raspberry Pi 4/5, Rockchip, AWS Graviton) using a lightweight K3s Kubernetes cluster. The Edge profile targets constrained environments with limited RAM, no GPU, and intermittent/disconnected network.

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│                  K3s Cluster                         │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  K3s Server  │  │  K3s Agent   │  │  K3s Agent │ │
│  │  (control)   │  │  (worker 1)  │  │  (worker 2)│ │
│  │  RPi5 8GB    │  │  RPi4 4GB    │  │  RPi4 4GB  │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │         │
│         └─────────────────┼─────────────────┘         │
│                           │                           │
│  ┌────────────────────────▼────────────────────────┐  │
│  │           SovereignStack Edge Stack               │  │
│  │  Gateway  │  Memory  │  llama.cpp  │  Ingest     │  │
│  │  (1 pod)  │  (1 pod) │  (1 pod)    │  (1 pod)    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Supporting Infrastructure                       │  │
│  │  MetalLB  │  Longhorn  │  Traefik  │  Prometheus│  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

---

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **CPU** | ARM Cortex-A72 (4 cores) | ARM Cortex-A76 (8 cores) |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 32 GB SD/SSD | 128 GB NVMe/SSD |
| **Network** | 100 Mbps | 1 Gbps |
| **GPU** | None (CPU inference only) | None (CPU inference only) |
| **Node count** | 1 (single-node) | 3 (HA cluster) |

### Supported ARM Boards

| Board | CPU | RAM | Storage | Status |
|---|---|---|---|---|
| Raspberry Pi 5 | Cortex-A76 (4c) | 8 GB | NVMe (via hat) | ✅ Tested |
| Raspberry Pi 4 | Cortex-A72 (4c) | 4-8 GB | SD/SSD | ✅ Tested |
| Rock 5B | Cortex-A76 (4c) + A55 (4c) | 16 GB | NVMe | ✅ Tested |
| Orange Pi 5 | Cortex-A76 (4c) + A55 (4c) | 16 GB | NVMe | ✅ Compatible |
| AWS Graviton (t4g) | ARM Neoverse | 2-16 GB | EBS | ✅ Tested |

---

## Quick Start

### 1. Install K3s

```bash
# On each node
curl -sfL https://get.k3s.io | sh -

# Verify
k3s kubectl get nodes
```

For air-gapped install, download the K3s binary and images in advance:

```bash
# On a connected machine
curl -Lo k3s https://github.com/k3s-io/k3s/releases/download/v1.32.2+k3s1/k3s-arm64
curl -Lo k3s-airgap-images-arm64.tar \
  https://github.com/k3s-io/k3s/releases/download/v1.32.2+k3s1/k3s-airgap-images-arm64.tar

# Copy to each node and install
scp k3s k3s-airgap-images-arm64.tar pi@node:/tmp/
ssh pi@node "sudo mv /tmp/k3s /usr/local/bin/ && sudo chmod +x /usr/local/bin/k3s"
ssh pi@node "sudo mkdir -p /var/lib/rancher/k3s/agent/images/ && sudo mv /tmp/k3s-airgap-images-arm64.tar /var/lib/rancher/k3s/agent/images/"
ssh pi@node "curl -sfL https://get.k3s.io | INSTALL_K3S_SKIP_DOWNLOAD=true sh -"
```

### 2. Install SovereignStack Helm chart

```bash
# Add repo
helm repo add sovereignstack https://charts.sovereignstack.ai
helm repo update

# Create namespace
k3s kubectl create namespace sovereign-stack

# Install with Edge profile
helm upgrade --install sovereign-stack sovereignstack/sovereignstack \
  --namespace sovereign-stack \
  --set profile=edge \
  --set inference.backend=llama.cpp \
  --set inference.model=Phi-3-mini-4k-instruct-q4.gguf \
  --set memory.storageClass=longhorn \
  --set network.airGapped=true
```

### 3. Verify

```bash
# Check pods
k3s kubectl get pods -n sovereign-stack

# Port-forward gateway
k3s kubectl port-forward -n sovereign-stack svc/gateway 8080:8080 &

# Health check
curl http://localhost:8080/health

# Inference
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-valid-token" \
  -d '{"model":"default","messages":[{"role":"user","content":"Hello"}],"oasa_compliance_lock":true}'
```

---

## Edge-Specific Configuration

### Inference: llama.cpp (CPU-only)

Edge nodes use llama.cpp instead of vLLM for CPU-efficient inference:

```yaml
runtime:
  engine: "llama.cpp"
  model: "Phi-3-mini-4k-instruct-q4.gguf"
  precision: "GGUF_Q4"
  threads: 4
  batch_size: 512
  ctx_size: 4096
```

### Resource Tuning

```yaml
edge:
  cpu_mem_ratio: "1:1"          # 1 GB RAM per CPU core
  max_parallel_requests: 2      # Limited concurrency on CPU
  swap_reserve_mb: 1024         # Reserve swap for OOM prevention
  watchdog_timeout_seconds: 60  # Restart unresponsive services
```

### Storage: Longhorn

Edge clusters use [Longhorn](https://longhorn.io) for replicated block storage:

```bash
k3s kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.8.0/deploy/longhorn.yaml
```

---

## Air-Gapped Edge

For fully disconnected edge deployments:

### Pre-load Steps

```bash
# 1. On connected machine, download all images
./scripts/pull-edge-images.sh

# 2. Save and transfer to edge cluster
docker save sovereignstack/gateway:2026.1 sovereignstack/memory:2026.1 | gzip > edge-images.tar.gz
scp edge-images.tar.gz pi@edge-node:/tmp/

# 3. On edge node, load images
docker load < /tmp/edge-images.tar.gz

# 4. Install SovereignStack with air-gapped mode
helm upgrade --install sovereign-stack sovereignstack/sovereignstack \
  --namespace sovereign-stack \
  --set network.airGapped=true \
  --set registry.mode=local
```

### Offline Model Management

```yaml
models:
  source: "local"                     # No Hugging Face downloads
  path: "/data/models"
  verify_sha256: true
  pre_loaded:
    - "Phi-3-mini-4k-instruct-q4.gguf"
```

---

## Monitoring

Deploy Prometheus + Grafana on the edge cluster:

```bash
# Install Prometheus Stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.scrapeInterval=30s \
  --set grafana.enabled=true

# Import SovereignStack dashboard
k3s kubectl apply -f https://raw.githubusercontent.com/Kubenew/SovereignStack/main/config/grafana/dashboard.json
```

---

## Production Edge Checklist

| Requirement | Check |
|---|---|
| K3s installed on all nodes | ☐ |
| At least one control-plane node | ☐ |
| Longhorn storage provisioned | ☐ |
| Model weights pre-downloaded | ☐ |
| Container images pre-cached (air-gapped) | ☐ |
| Prometheus + alerting configured | ☐ |
| Log aggregation (Loki or Fluentd) | ☐ |
| Backup schedule configured | ☐ |
| Watchdog / auto-recovery enabled | ☐ |
| Network policy applied | ☐ |

---

## Limitations

| Constraint | Impact | Mitigation |
|---|---|---|
| CPU-only inference | ~2-5 tok/s (Phi-3 Q4 on RPi5) | Use quantized GGUF models |
| Limited RAM | May OOM with large context | Limit ctx_size to 2048 |
| SD card durability | Write wear on audit logs | Use SSD or Longhorn |
| No GPU | No INT4/AWQ, no flash attention | llama.cpp GGUF only |
| Network bandwidth | Slow image pulls | Pre-cache all images |

---

## See Also

- [Deployment Profiles](/docs/deployment/profiles.md)
- [Docker Compose Guide](/docs/deployment/docker-compose.md)
- [Docker Compose Production Template](/deploy/docker-compose.prod.yml)
- [Helm Guide](/docs/deployment/helm.md)
- [Runtime Configuration](/docs/runtime/index.md)
