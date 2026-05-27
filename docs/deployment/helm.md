# Helm / Kubernetes Deployment

For production, air-gapped, and datacenter deployments. The Helm chart provides full lifecycle management with NetworkPolicies, gVisor sandboxing, and multi-GPU tensor parallelism.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Gateway │  │ vLLM    │  │ Ingest  │  │ Memory  │       │
│  │ Pod     │  │ Pod     │  │ Pod     │  │ Pod     │       │
│  │ OPA     │  │ gVisor  │  │         │  │         │       │
│  │ Sidecar │  │ Sandbox │  │         │  │         │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │             │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐       │
│  │ Service │  │ Service │  │ Service │  │ Service │       │
│  │ :8080   │  │ :8000   │  │ :8081   │  │ :8082   │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│  ┌───────────────┐  ┌──────────────────────┐               │
│  │ PVC: Models   │  │ NetworkPolicy        │               │
│  │ PVC: Data     │  │ (Zero Egress)        │               │
│  └───────────────┘  └──────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Kubernetes 1.28+
- Helm 3.14+
- NVIDIA GPU Operator (for GPU nodes)
- CSI driver with encryption support (optional)

---

## Installation

```bash
# Add the repo
helm repo add sovereign-stack https://kubenew.github.io/SovereignStack/charts
helm repo update

# Install the chart
helm install sovereign-stack ./charts/sovereignstack \
  --namespace sovereign-stack --create-namespace \
  --set vllm.model.name="Qwen/Qwen2.5-7B-Instruct" \
  --set global.air_gapped=true
```

---

## Configuration

### Values Reference

| Parameter | Default | Description |
|---|---|---|
| `global.air_gapped` | `false` | Enable air-gapped mode (no WAN access) |
| `vllm.model.name` | `Qwen/Qwen2.5-7B-Instruct` | Model to serve |
| `vllm.model.precision` | `INT4_AWQ` | Quantization format |
| `vllm.gpu.count` | `1` | GPU count for tensor parallelism |
| `vllm.gpu.memory_utilization` | `0.90` | GPU memory utilization |
| `vllm.max_model_len` | `4096` | Max context length |
| `gateway.replicaCount` | `2` | Gateway replicas (HA) |
| `gateway.auth.enabled` | `true` | Enable OIDC auth |
| `gateway.policy.enabled` | `true` | Enable OPA policy engine |
| `networkPolicy.enabled` | `true` | Enable NetworkPolicies |
| `sandbox.runtime` | `gvisor` | Container runtime (`gvisor`, `kata`, `runc`) |

### Air-Gapped Configuration

```bash
helm upgrade --install sovereign-stack ./charts/sovereignstack \
  --namespace sovereign-stack \
  --set global.air_gapped=true \
  --set networkPolicy.egressDenyAll=true \
  --set vllm.model.source="local" \
  --set vllm.model.path="/data/models/Qwen2.5-7B-Instruct"
```

### Multi-GPU Tensor Parallelism

```bash
helm upgrade --install sovereign-stack ./charts/sovereignstack \
  --namespace sovereign-stack \
  --set vllm.gpu.count=4 \
  --set vllm.gpu.memory_utilization=0.95 \
  --set vllm.max_model_len=32768
```

---

## Network Policies

The Helm chart deploys strict NetworkPolicies by default:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sovereign-stack-default-deny
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sovereign-stack-allow-internal
spec:
  podSelector: {}
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: sovereign-stack
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: sovereign-stack
```

---

## Persistent Storage

| PVC | Size | Access Mode | Purpose |
|---|---|---|---|
| `models` | 100 Gi | ReadOnlyMany | Model weight storage |
| `data` | 50 Gi | ReadWriteOnce | Vector DB, audit logs |

---

## Monitoring

The chart exposes Prometheus metrics on all services:

```bash
kubectl port-forward -n sovereign-stack service/gateway 8080:8080
curl http://localhost:8080/metrics
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| CrashLoopBackOff on vLLM | GPU not available | Check `kubectl describe pod -n sovereign-stack -l app=vllm` for GPU errors |
| Gateway timeout | vLLM not ready | Increase `startPeriod` in vLLM health check |
| NetworkPolicy blocking | Pod cross-namespace | Ensure all pods are in `sovereign-stack` namespace |
| Model download fails | Air-gapped + no local mirror | Pre-load model to PVC: `kubectl cp model.bin sovereign-stack/vllm-0:/data/models/` |
