# RFC-0040: Model Lineage Protocol

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0005, RFC-0013, RFC-0020

## Abstract

Defines the Model Lineage Protocol (MLP) for tracking the complete provenance chain of AI models — from training data through fine-tuning to inference. Enables AI Bill of Materials (AI BOM) generation, model lineage audits, and supply chain verification.

## Specification

### URI Schemes

| Scheme | Purpose | Example |
|--------|---------|---------|
| `model://` | AI model identifier | `model://huggingface/Qwen/Qwen2.5-72B` |
| `dataset://` | Training/evaluation dataset | `dataset://huggingface/c4` |
| `training://` | A specific training run | `training://zcube-a/run-0042` |
| `evaluation://` | A model evaluation | `evaluation://zcube-a/eval-007` |

### Lineage Graph

```
dataset://common-crawl ──┐
                          ├──→ training://pre-training-001 ──→ model://qwen-base
dataset://code-stack  ───┘                                              │
                                                                         ├──→ training://sft-042 ──→ model://qwen-sft
dataset://instructions ────────────────────────────────────────────────┘       │
                                                                                ├──→ evaluation://harness-eval-007 → evaluation report
                                                                                │
                                                                                ├──→ training://rlhf-015 ──→ model://qwen-rlhf
                                                                                │
                                                                                └──→ deployment → inference://session-abc
```

### Model Object

```json
{
  "id": "model://zcube-a/qwen2.5-72b/v3.1.0",
  "name": "Qwen2.5-72B",
  "architecture": "transformer-decoder",
  "parameters_b": 72,
  "quantization": "fp16",
  "hash": "cas://sha256:a1b2c3...",
  "lineage": {
    "base_model": "model://qwen/qwen2.5-72b-base",
    "training_runs": ["training://zcube-a/sft-042", "training://zcube-a/rlhf-015"],
    "datasets": ["dataset://common-crawl", "dataset://code-stack", "dataset://instructions"]
  },
  "compliance": {
    "license": "apache-2.0",
    "jurisdiction": "CN",
    "restrictions": ["export_control"]
  }
}
```

### Training Run

```json
{
  "id": "training://zcube-a/sft-042",
  "model": "model://qwen/qwen2.5-72b-base",
  "dataset": "dataset://instructions/v2.1",
  "hyperparameters": {"learning_rate": 2e-5, "batch_size": 128, "epochs": 3},
  "compute": {"gpu_hours": 2048, "hardware": "H100-80GB", "cluster": "zcube-a"},
  "provenance": {"operator": "agent://training-pipeline", "audit": "audit://..."},
  "resulting_model": "model://zcube-a/qwen2.5-72b/v3.1.0"
}
```

### Evaluation Record

```json
{
  "id": "evaluation://zcube-a/eval-007",
  "model": "model://zcube-a/qwen2.5-72b/v3.1.0",
  "benchmark": "open_llm_leaderboard",
  "metrics": {"mmlu": 0.85, "gsm8k": 0.78, "human_eval": 0.72},
  "dataset_version": "dataset://harness/v1",
  "provenance": {"operator": "agent://eval-runner", "timestamp": "2026-06-03T12:00:00Z"}
}
```

### AI Bill of Materials (AI BOM)

```json
{
  "id": "bom://zcube-a/qwen2.5-72b-deployment",
  "model": "model://zcube-a/qwen2.5-72b/v3.1.0",
  "components": [
    {"type": "base_model", "id": "model://qwen/qwen2.5-72b-base", "license": "apache-2.0"},
    {"type": "dataset", "id": "dataset://instructions/v2.1", "license": "mit"},
    {"type": "fine_tune", "id": "training://zcube-a/sft-042", "framework": "axolotl"},
    {"type": "plugin", "id": "ext://data-validator/v1.2.0", "vendor": "sovereign-ai"},
    {"type": "runtime", "id": "node://zcube-a/gpu-003", "runtime": "vllm-0.6.0"}
  ],
  "signature": "ed25519:base64url..."
}
```

## Core Types

```rust
pub struct ModelObject { pub id: String, pub architecture: String, pub parameters_b: f64, pub hash: String, pub lineage: ModelLineage, pub compliance: ModelCompliance }
pub struct TrainingRun { pub id: String, pub model: String, pub dataset: String, pub hyperparameters: HashMap<String, f64>, pub compute: ComputeSpec, pub resulting_model: String }
pub struct EvaluationRecord { pub id: String, pub model: String, pub benchmark: String, pub metrics: HashMap<String, f64> }
pub struct AiBom { pub id: String, pub model: String, pub components: Vec<BomComponent> }
pub struct BomComponent { pub component_type: String, pub id: String, pub license: String }
```

## Conformance Impact

- Required for **Level 3 (Knowledge)** conformance
- Enables AI BOM generation for supply chain audits
- Foundation for ISO 42001 / EU AI Act compliance evidence
