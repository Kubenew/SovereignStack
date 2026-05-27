# RFC 0001: Sovereign Runtime Specification

| Field | Value |
|---|---|
| **Status** | Draft |
| **Author** | SovereignStack Core Team |
| **Created** | 2026-05-27 |
| **Category** | Standards Track |

---

## Summary

Define the Sovereign Runtime — the AI execution layer responsible for model loading, inference, scheduling, resource isolation, and OpenAI-compatible API serving.

---

## Motivation

Currently, the runtime implementation is tightly coupled to vLLM. While vLLM is an excellent engine, the project needs a **runtime abstraction** that allows:

- Multiple backend engines (vLLM, llama.cpp, TensorRT-LLM, ONNX Runtime)
- Consistent API contract regardless of backend
- Pluggable model routing and scheduling
- Resource-aware deployment profiles
- Reproducible inference behavior

---

## Design

### Architecture

```
                    ┌─────────────────────────────┐
                    │     OpenAI-Compatible API    │
                    │  POST /v1/chat/completions   │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │      RUNTIME GATEWAY         │
                    │  Auth · Policy · Routing    │
                    │  Model Selection · Fallback  │
                    └────────────┬────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
     │   vLLM Engine    │ │ llama.cpp   │ │ Future Engine   │
     │  PagedAttention  │ │ GGUF/CPU    │ │ (pluggable)     │
     │  AWQ/FP8/INT4    │ │ Edge/ARM    │ │                 │
     └─────────────────┘ └─────────────┘ └─────────────────┘
```

### Runtime API

The runtime MUST expose the following endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/v1/chat/completions` | POST | Chat completion (OpenAI-compatible) |
| `/v1/models` | GET | List available models |
| `/health` | GET | Liveness probe |
| `/metrics` | GET | Prometheus metrics |

### Runtime Configuration

```yaml
runtime:
  engine: "vllm"                         # vllm | llama.cpp | tensorrt-llm
  model: "Qwen/Qwen2.5-7B-Instruct"      # Model name or path
  precision: "INT4_AWQ"                  # INT4_AWQ | FP8 | FP16 | GGUF_Q4
  max_tokens: 4096                       # Max context length
  gpu_memory_utilization: 0.90           # 0.0 - 1.0
  tensor_parallel: 1                     # GPU count for TP
  enable_flash_attention: true
  enforce_air_gapped: true               # No WAN access
```

### Model Lifecycle

```
Download → Verify SHA-256 → Verify Cosign Signature → Load → Serve → Unload
```

| Stage | Validation |
|---|---|
| Download | Checksum from manifest |
| Verify | SHA-256 match against signed metadata |
| Cosign | Signature verification via public key |
| Load | Memory-mapped, locked in VRAM |
| Serve | Available via `/v1/chat/completions` |
| Unload | Graceful shutdown, cache eviction |

---

## Security Considerations

- Model weights MUST be verified before loading
- Runtime MUST run inside gVisor/Kata sandbox
- No network egress from runtime container
- GPU memory isolation between concurrent requests (vLLM PagedAttention)
- Runtime health MUST be monitored via `/health` endpoint

---

## Compatibility

- Backward compatible with existing `docker-compose.yml` and Helm chart
- OpenAI API compatibility is REQUIRED
- Backends MAY extend the API with engine-specific endpoints

---

## Deployment Strategy

| Profile | Recommended Engine | Precision |
|---|---|---|
| Edge | llama.cpp | GGUF Q4 |
| Air-Gapped | vLLM | INT4 AWQ |
| Datacenter | vLLM | FP8 / INT4 |
| Personal | llama.cpp | GGUF Q4 |

---

## Migration Path

Existing deployments using `docker-compose.yml` or Helm continue to work. The runtime engine selection is opt-in via `sovereign-stack.yaml` configuration.

---

## Alternatives Considered

| Alternative | Reason Not Selected |
|---|---|
| Single engine lock-in | Limits deployment flexibility |
| Custom inference server | Unnecessary engineering; existing engines are mature |
| No runtime abstraction | Architecture drift risk |

---

## References

- [vLLM Documentation](https://docs.vllm.ai)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
