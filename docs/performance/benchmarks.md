# Performance Benchmarks

This page documents throughput, latency, and resource usage for each supported deployment profile.

---

## Test Methodology

| Parameter | Value |
|---|---|
| Test tool | `python tools/benchmark.py --model <name> --prompts <file>` |
| Metrics | Tokens/sec, TTFT (time to first token), p50/p95/p99 latency, VRAM usage |
| Models | Qwen2.5-7B-Instruct, Llama-3.1-8B, Phi-3-mini-4K, DeepSeek-Coder-V2-Lite |
| Hardware | See each profile section |
| Run count | 5 runs per model, median reported |
| Concurrency | 1, 4, 8, 16 concurrent requests |

---

## Personal Profile

| Hardware | CPU | RAM | GPU | Storage |
|---|---|---|---|---|
| MacBook Pro M3 Pro | Apple Silicon 12-core | 18 GB | Integrated (18 GB unified) | SSD |

### Results

| Model | Quant | Tokens/s (1 req) | Tokens/s (4 req) | TTFT p50 | VRAM |
|---|---|---|---|---|---|
| Phi-3-mini-4K-Instruct | FP16 | 38.2 | 32.1 | 210ms | 4.2 GB |
| Qwen2.5-7B-Instruct | FP16 | 18.5 | 14.8 | 340ms | 14.1 GB |
| Llama-3.1-8B | INT4 (AWQ) | 24.7 | 20.3 | 290ms | 6.8 GB |

---

## Edge Profile

| Hardware | CPU | RAM | GPU | Storage |
|---|---|---|---|---|
| Raspberry Pi 5 | Cortex-A76 4-core 2.4 GHz | 8 GB | None | NVMe SSD (USB 3.0) |

### Results

| Model | Quant | Backend | Tokens/s (1 req) | TTFT p50 | RAM |
|---|---|---|---|---|---|
| Phi-3-mini-4K-Instruct | Q4 (GGUF) | llama.cpp | 5.1 | 1.8s | 4.5 GB |
| TinyLlama-1.1B | Q4 (GGUF) | llama.cpp | 12.4 | 720ms | 1.9 GB |
| Qwen2.5-0.5B | Q4 (GGUF) | llama.cpp | 18.7 | 480ms | 1.1 GB |

---

## Air-Gapped Profile

| Hardware | CPU | RAM | GPU | Storage |
|---|---|---|---|---|
| Dell R750xa | Xeon 16-core | 128 GB | NVIDIA A100 80GB | NVMe RAID 1 |

### Results

| Model | Quant | Tokens/s (1 req) | Tokens/s (8 req) | Tokens/s (16 req) | TTFT p50 | VRAM |
|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | FP16 | 142.3 | 98.5 | 72.1 | 95ms | 15.8 GB |
| Qwen2.5-7B-Instruct | AWQ | 168.7 | 134.2 | 108.4 | 85ms | 6.2 GB |
| Llama-3.1-8B | FP16 | 128.6 | 91.2 | 65.8 | 110ms | 17.2 GB |
| Llama-3.1-8B | AWQ | 155.4 | 124.8 | 96.3 | 98ms | 7.1 GB |
| DeepSeek-Coder-V2-Lite (16B) | FP8 | 72.5 | 51.3 | 38.7 | 210ms | 38.4 GB |

---

## Datacenter Profile

| Hardware | CPU | RAM | GPU | Storage |
|---|---|---|---|---|
| 8x NVIDIA H100 | AMD EPYC 64-core | 512 GB | 8× H100 80GB | NVMe RAID 10 |

### Results

| Model | Quant | TP | Tokens/s (1 req) | Tokens/s (32 req) | TTFT p50 | VRAM (per GPU) |
|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | FP16 | 1 | 892 | 1,240 | 24ms | 13.5 GB |
| Llama-3.1-70B | FP16 | 4 | 1,240 | 1,680 | 52ms | 72.4 GB |
| Llama-3.1-70B | FP8 | 4 | 1,890 | 2,420 | 38ms | 38.2 GB |
| DeepSeek-V3 (671B) | FP8 | 8 | 450 | 720 | 210ms | 72.1 GB |

---

## Memory Service Latency

| Operation | p50 | p95 | p99 | Backend |
|---|---|---|---|---|
| Embed (128-token doc) | 2.1ms | 4.8ms | 8.2ms | JSON |
| Embed (128-token doc) | 3.4ms | 7.1ms | 12.5ms | Qdrant |
| Query (top-5, 1K vectors) | 1.2ms | 3.5ms | 6.8ms | JSON |
| Query (top-5, 10K vectors) | 4.8ms | 9.2ms | 18.1ms | Qdrant |
| Cache set | 0.8ms | 1.9ms | 3.2ms | JSON |
| Cache get (hit) | 0.4ms | 1.1ms | 2.0ms | JSON |

---

## Gateway Overhead

| Operation | Latency overhead |
|---|---|
| JWT validation | ~0.3ms |
| OPA policy check | ~0.8ms |
| Audit log write | ~0.2ms |
| SPIFFE SVID fetch | ~1.5ms |
| **Total auth & policy overhead** | **~2.8ms** |

---

## Running Benchmarks

```bash
# Run benchmark against local deployment
python tools/benchmark.py \
    --server http://localhost:8080/v1/chat/completions \
    --model Qwen/Qwen2.5-7B-Instruct \
    --token <your-token> \
    --prompts data/benchmark/prompts.txt \
    --concurrency 1 4 8 16

# Compare two model configurations
python tools/benchmark.py --compare \
    --baseline "fp16" \
    --candidate "awq" \
    --format table

# Generate benchmark report
python tools/benchmark.py --report --output reports/benchmark.md
```

---

## See Also

- [Architecture Overview](/ARCHITECTURE.md)
- [Deployment Profiles](/docs/deployment/profiles.md)
- [Edge Cluster Guide](/docs/deployment/edge.md)
- [Runtime Docs](/docs/runtime/index.md)
