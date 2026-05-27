# Deployment Profiles

Each profile is optimized for a specific operational context. Choose the profile that matches your hardware, network, and security requirements.

---

## Personal

**Target:** Individual developer workstation or homelab.

### Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 32 GB |
| GPU | None (CPU OK) | RTX 3090 / Apple M-series |
| Disk | 10 GB | 50 GB |
| Network | Internet (for model download) | — |

### Configuration

```yaml
node_infrastructure:
  engine: "docker-compose"
  air_gapped_enforcement: false  # Internet allowed for model download
  network_isolation:
    allow_wan: true

compute_execution:
  precision: "INT4_GGUF"
  hardware:
    vram_budget_gb: 8
    allow_cpu_fallback: true
```

### Best For
- Local AI assistant
- Development and testing
- Learning the platform

---

## Edge

**Target:** ARM devices (Raspberry Pi, Jetson), IoT gateways, low-power nodes.

### Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| RAM | 4 GB | 16 GB |
| GPU | None | Jetson Orin / Apple Silicon |
| Disk | 4 GB | 32 GB |
| Network | Disconnected | Occasional sync |

### Configuration

```yaml
node_infrastructure:
  engine: "docker-compose"
  air_gapped_enforcement: true

compute_execution:
  precision: "INT4_GGUF"
  optimization_engine: "llama.cpp"
  hardware:
    accelerator: "CPU"
    vram_budget_gb: 4
    allow_cpu_fallback: true
```

### Best For
- Field deployments
- Remote sensors and automation
- Offline AI assistants

---

## Air-Gapped

**Target:** Isolated networks with no internet access. Government, defense, regulated industry.

### Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 64 GB |
| GPU | RTX 4090 | A100 / H100 |
| Disk | 50 GB | 200 GB |
| Network | No WAN | Internal fabric only |

### Configuration

```yaml
node_infrastructure:
  engine: "k3s"
  air_gapped_enforcement: true
  storage:
    ephemeral_encrypted: true
    encryption_algorithm: "AES-256-GCM"
    hardware_tpm_binding: true
  network_isolation:
    allow_wan: false
    dns_mode: "LOCAL_ONLY"

compute_execution:
  precision: "INT4_AWQ"
  optimization_engine: "vLLM"
  runtime_protection:
    enforce_compliance_lock: true
```

### Best For
- Classified environments
- Regulated financial services
- Healthcare (HIPAA)

---

## Datacenter

**Target:** Multi-node GPU clusters with HA and federation.

### Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| RAM | 64 GB | 512 GB |
| GPU | 4x A100 | 8x H100 |
| Disk | 500 GB | 2 TB NVMe |
| Network | 25 Gbps fabric | 100 Gbps |

### Configuration

```yaml
node_infrastructure:
  engine: "kubernetes"
  air_gapped_enforcement: true

compute_execution:
  precision: "FP8"
  optimization_engine: "vLLM"
  hardware:
    accelerator: "NVIDIA_CUDA"
    vram_budget_gb: 80
    allow_cpu_fallback: false
  runtime_protection:
    memory_leak_threshold_mb: 1024
    max_token_context: 32768
```

### Best For
- Enterprise AI workloads
- Federated multi-node inference
- Large-scale model serving
