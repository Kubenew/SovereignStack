# Sovereign Runtime

The runtime layer is responsible for AI model execution, inference routing, resource scheduling, and runtime isolation.

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │     OpenAI-Compatible API    │
                    │  POST /v1/chat/completions   │
                    │  GET /v1/models              │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │      RUNTIME GATEWAY          │
                    │  Auth · Policy · Routing     │
                    │  Model Selection · Fallback   │
                    │  Audit Logging · Tracing      │
                    └────────────┬────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
     │   vLLM Engine    │ │ llama.cpp   │ │ TensorRT-LLM    │
     │  GPU, Multi-GPU  │ │ CPU, ARM    │ │ NVIDIA Optimized│
     │  PagedAttention  │ │ GGUF models │ │ FP8/INT4/INT8   │
     │  AWQ/FP8/INT4    │ │ Edge deploy │ │                 │
     └─────────────────┘ └─────────────┘ └─────────────────┘
```

---

## Engine Support

| Engine | Status | Precision | Hardware | Use Case |
|---|---|---|---|---|
| **vLLM** | ✅ Production | FP8, INT4 AWQ, FP16 | NVIDIA GPU | Datacenter, Air-Gapped |
| **llama.cpp** | 🚧 Beta | GGUF Q4, Q8 | CPU, ARM, GPU | Edge, Personal |
| **TensorRT-LLM** | 📅 Planned | FP8, INT4, INT8 | NVIDIA GPU | Large-scale inference |

---

## API Contract

All runtimes MUST expose the OpenAI-compatible API:

### `POST /v1/chat/completions`

```json
{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a sovereign AI assistant."},
    {"role": "user", "content": "What is digital sovereignty?"}
  ],
  "temperature": 0.2,
  "max_tokens": 1024,
  "stream": false
}
```

### `GET /v1/models`

```json
{
  "object": "list",
  "data": [
    {"id": "Qwen/Qwen2.5-7B-Instruct", "object": "model", "created": 1716800000, "owned_by": "sovereign"}
  ]
}
```

### `GET /health`

```json
{"status": "ok", "service": "runtime", "engine": "vllm", "model": "Qwen/Qwen2.5-7B-Instruct"}
```

---

## Model Lifecycle

```
Download ──→ Verify ──→ Load ──→ Serve ──→ Unload
```

| Stage | Action | Validation |
|---|---|---|
| **Download** | Pull from registry or local file | SHA-256 checksum |
| **Verify** | Validate integrity | SHA-256 + Cosign signature |
| **Load** | Load into GPU memory | Memory budget check |
| **Serve** | Accept inference requests | Health check |
| **Unload** | Graceful teardown | Cache flush |

---

## Resource Scheduling

### GPU Memory

- **vLLM:** PagedAttention for dynamic memory allocation
- **Budget:** Configurable via `vram_budget_gb` or `gpu_memory_utilization`
- **OOM Protection:** Request queue depth limit, adaptive context sizing

### Request Queue

```
Client → Rate Limiter → Queue → Scheduler → Engine
```

| Queuing | Strategy | Default |
|---|---|---|
| Max queue depth | FIFO with priority lanes | 128 |
| Timeout | Per-request deadline | 30s |
| Scheduling | Maximum parallel tokens | Auto (vLLM) |

---

## Runtime Configuration

```yaml
runtime:
  engine: "vllm"
  model: "Qwen/Qwen2.5-7B-Instruct"
  precision: "INT4_AWQ"
  max_context: 4096
  gpu_memory_utilization: 0.90
  tensor_parallel: 1
  enable_flash_attention: true
```

---

## See Also

- [RFC-0003: Session Runtime](/rfcs/RFC-0003-session-runtime.md)
- [Deployment Profiles](/docs/deployment/profiles.md)
- [vLLM Documentation](https://docs.vllm.ai)
