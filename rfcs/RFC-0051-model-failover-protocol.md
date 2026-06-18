# RFC-0051: Model Failover Protocol

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0050, RFC-0040

## Abstract

Defines the Model Failover Protocol (MFP) for automatic policy-driven switching between primary, fallback, and emergency models during inference failures.

## Specification

### Failover Chain

```json
{
  "primary": "model://qwen3-235b",
  "fallback": "model://qwen3-72b",
  "emergency": "model://llama4-70b",
  "fallback_policy": {
    "trigger_on": ["timeout", "error_rate > 0.05", "latency_p99 > 5000ms", "model_unavailable"],
    "auto_rollback": true,
    "quality_check_after_switch": true,
    "escalate_after_seconds": 300
  }
}
```

### Failover Event Log

```json
{
  "id": "failover://zcube-a/2026-06-03/evt-001",
  "timestamp": "2026-06-03T12:00:00Z",
  "trigger": "model_unavailable",
  "from": "model://qwen3-235b",
  "to": "model://qwen3-72b",
  "decision_time_ms": 120,
  "quality_drop_pct": 8,
  "auto_rollback": false
}
```

### Switching Strategies

| Strategy | Latency | Quality Preservation | Use Case |
|----------|---------|---------------------|----------|
| Cold switch | <100ms | None — new session | Emergency failover |
| Warm switch | <500ms | KV cache preserved (same architecture) | Planned fallback |
| Progressive | 1-5s | Gradual traffic migration | Zero-downtime |

## Core Types

```rust
pub struct FailoverChain { pub primary: String, pub fallback: String, pub emergency: String, pub policy: FailoverPolicy }
pub struct FailoverEvent { pub id: String, pub trigger: String, pub from: String, pub to: String, pub decision_time_ms: u64 }
pub enum FailoverStrategy { Cold, Warm, Progressive }
```
