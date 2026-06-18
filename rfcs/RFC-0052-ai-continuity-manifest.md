# RFC-0052: AI Continuity Manifest

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0050, RFC-0051

## Abstract

Defines the AI Continuity Manifest — a `continuity://` object that declares a service's recovery configuration, fallback model chain, continuity scoring criteria, and compliance evidence.

## Specification

### Continuity Manifest Object

```json
{
  "id": "continuity://zcube-a/legal-agent/v2",
  "service": "legal-agent",
  "version": "2.0.0",
  "owner": "agent://legal-team",
  "primary_model": "model://qwen3-235b",
  "fallback_models": [
    "model://qwen3-72b",
    "model://llama4-70b",
    "model://mistral-large-2"
  ],
  "max_quality_degradation": 15,
  "max_downtime_seconds": 30,
  "ai_rto_seconds": 30,
  "ai_rpo_seconds": 1,
  "strategies": ["warm", "cold"],
  "recovery_playbooks": [
    "playbook://zcube-a/gpu-failure",
    "playbook://zcube-a/network-partition",
    "playbook://zcube-a/model-corruption"
  ],
  "dependencies": {
    "model_providers": ["huggingface", "together"],
    "hardware_required": ["NVIDIA_H100", "AMD_MI350"],
    "min_compliance_level": "SECURE_L2"
  },
  "continuity_score": 92,
  "last_failover_test": "2026-05-15T12:00:00Z",
  "last_reviewed": "2026-06-01T12:00:00Z",
  "signature": "ed25519:base64url..."
}
```

### Continuity Score Calculation

| Factor | Weight | Source |
|--------|--------|--------|
| Fallback models defined | 25% | Manifest field |
| Portability tested | 25% | `recovery://` logs |
| Recovery playbooks present | 20% | `playbook://` list |
| Recent failover test | 15% | Last test date |
| Provider diversity | 15% | `dependencies.model_providers` count |

### Core Types

```rust
pub struct ContinuityManifest { pub id: String, pub service: String, pub primary_model: String, pub fallback_models: Vec<String>, pub recovery_playbooks: Vec<String>, pub continuity_score: f64 }
pub struct ContinuityScore { pub score: f64, pub factors: HashMap<String, f64> }
```
