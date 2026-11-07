# AWS Neuron Accelerator Adapter for SovereignStack

Production-grade SovereignStack accelerator adapter for AWS Neuron (Inferentia & Trainium) hardware.
Engineered for local-first, air-gapped sovereign AI infrastructure governed by the Open Architecture Specification for Autonomous and Sovereign AI (**OASA v0.6 / RFC-0075 / RFC-0077**).

It is safe to import on any operating system or machine without AWS Neuron hardware or drivers installed.

---

## 1. Supported Framework Families

| Framework | Target Hardware | Neuron Core Arch | Primary Mechanism | SovereignStack Status |
|---|---|---|---|---|
| **Native TorchNeuron** | Trainium 2 (`trn2`), Trainium 3 (`trn3`) | `NeuronCore-v3` | PyTorch custom `neuron` device + `torch.compile` | **Supported (Production)** |
| **Torch-NeuronX** | Inferentia 2 (`inf2`), Trainium 1 (`trn1`, `trn1n`), Trainium 2 (`trn2`) | `NeuronCore-v2` | OpenXLA / `torch_xla` device + `torch_neuronx.trace()` | **Supported (Production)** |
| **Torch-Neuron (Legacy)** | Inferentia 1 (`inf1`) | `NeuronCore-v1` | `torch.neuron.trace()` + TorchScript NEFF artifacts | **Supported (Archived JIT loader & trace)** |

Official AWS Neuron Documentation: https://awsdocs-neuron.readthedocs-hosted.com/en/latest/frameworks/torch/index.html

---

## 2. Core Security & Governance Guarantees

In accordance with SovereignStack foundation principles:

1. **Anti-Theater Invariant**:
   Accelerator hardware is never invoked unless an OASA policy authorization returns `allow`. Denied requests fail fast with `NeuronAuthorizationError` before touching any hardware, driver, or VRAM resources.
2. **Fail-Closed by Default**:
   If Neuron hardware is requested or configured, missing hardware or compilation errors fail closed (`NeuronUnavailable`). There is no silent fallback to CPU unless explicitly enabled via `allow_cpu_fallback=True`.
3. **Cryptographic Provenance**:
   Every model load, compile, trace, and inference operation appends an immutable, SHA-256 hash-chained event to the provenance ledger.
4. **Independent Evidence Package**:
   Generates verifiable OASA L3 compliance artifacts (`oasa-profile://accelerator-neuron/v0.1`) containing cryptographic proofs of authorization, provenance integrity, and hardware telemetry.
5. **Artifact Integrity Verification**:
   Precompiled TorchScript / NEFF binary artifacts are checked against expected SHA-256 digests prior to ingestion into the execution graph.

---

## 3. Architecture & Adapter Contract

The integration adheres to SovereignStack's 5-stage governance pipeline:

```
┌─────────────┐    ┌────────────────┐    ┌───────────────┐    ┌──────────────────────┐    ┌────────────────────┐
│ 1. Identity │ ──▶│ 2. Capability  │ ──▶│   3. Policy   │ ──▶│    4. Provenance     │ ──▶│    5. Evidence     │
│   Mapper    │    │     Mapper     │    │  (Anti-Theater│    │ (SHA-256 Chained Log)│    │ (OASA L3 Package)  │
└─────────────┘    └────────────────┘    └───────┬───────┘    └──────────────────────┘    └────────────────────┘
                                                 │
                                           [ALLOW ONLY]
                                                 ▼
                                     ┌───────────────────────┐
                                     │  AWS Neuron Hardware  │
                                     │ (Trn1/Trn2/Inf1/Inf2) │
                                     └───────────────────────┘
```

---

## 4. Quickstart & Runtime Examples

### 4.1 Auto-Detection and Health Check

```python
from integrations.accelerators.aws_neuron import NeuronBackend, NeuronConfig

backend = NeuronBackend(NeuronConfig(mode="auto"))
health = backend.health()
print(health)
# Output:
# {
#     "backend": "aws-neuron",
#     "version": "0.2.0",
#     "available": True,
#     "framework": "native",
#     "device": "neuron",
#     "device_count": 2,
#     "hardware_generation": "validate Trn2/Trn3 SKU and SDK",
#     "execution_enabled": True,
#     "policy_enforced": False,
#     "provenance_chain_length": 0
# }
```

### 4.2 Native Model Loading & Compilation

```python
from integrations.accelerators.aws_neuron import NeuronBackend, NeuronConfig

backend = NeuronBackend(NeuronConfig(mode="native", compile_model=True))
# Loads eager PyTorch model directly to the 'neuron' custom device and applies torch.compile
model = backend.load_model(model)
```

### 4.3 Tracing & Compiling Models (`torch_neuronx` and `torch.neuron`)

```python
from integrations.accelerators.aws_neuron import NeuronBackend, NeuronConfig

# Works for both torch-neuronx (Inf2/Trn1) and legacy torch-neuron (Inf1)
backend = NeuronBackend(NeuronConfig(mode="legacy"))
wrapped_model = backend.trace_model(eager_model, example_inputs=sample_tensor)

# Execute inference through the managed wrapper
result = wrapped_model(sample_tensor)
```

### 4.4 Loading Precompiled NEFF / TorchScript Artifacts with Hash Verification

```python
from integrations.accelerators.aws_neuron import NeuronBackend, NeuronConfig

backend = NeuronBackend(NeuronConfig(mode="auto"))
compiled_model = backend.load_compiled_artifact(
    "models/llama3_inf2.pt",
    expected_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
output = compiled_model(input_tokens)
```

### 4.5 Governed Inference with Policy, Provenance & Evidence

```python
from integrations.accelerators.aws_neuron import (
    NeuronBackend,
    NeuronConfig,
    NeuronPolicyAdapter,
    NeuronProvenanceRecorder,
)

policy = NeuronPolicyAdapter()
provenance = NeuronProvenanceRecorder()

backend = NeuronBackend(
    NeuronConfig(mode="native", enforce_policy=True, record_provenance=True),
    policy_adapter=policy,
    provenance_recorder=provenance,
)

# 1. Governed load (fails if context violates security policy)
model = backend.load_model(eager_model, context={"security_tier": "air-gapped"})

# 2. Governed inference with automatic device synchronization
output = backend.infer(model, input_tensor)

# 3. Independent audit evidence generation
evidence_package = backend.generate_evidence(
    workload_uri="model://sovereign-qwen",
    operation="accelerator:neuron:infer"
)
assert evidence_package["conformance"]["accelerator-neuron-0.1"] == "PASS"
```

### 4.6 Workload Routing & Placement

```python
from integrations.accelerators.aws_neuron import NeuronModelRouter

router = NeuronModelRouter()
decision = router.route_workload(
    model_name="Llama-3.1-70B",
    precision="bfloat16",
    hardware_info={"total_cores": 24, "total_memory_gb": 384.0, "generation": "NeuronCore-v2"}
)

print(decision)
# RouteDecision(
#     allowed=True,
#     backend="aws-neuron",
#     framework="native",
#     target_device="neuron",
#     required_cores=8,
#     estimated_memory_gb=140.0,
#     recommended_sku="inf2.24xlarge",
#     reason="Workload fits within NeuronCore compute and memory specifications"
# )
```

---

## 5. Sovereign Node Manifest (`sovereign-stack.yaml`)

To target AWS Neuron in your sovereign appliance configuration:

```yaml
version: "2026.1"
metadata:
  name: "sovereign-enterprise-appliance"
  compliance_profile: "OASA-STRICT-GDPR-HIPAA"

compute_execution:
  gateway: "turboprivate-ai-proxy"
  optimization_engine: "TurboQuant-Neuron"
  precision: "BFLOAT16"
  hardware:
    accelerator: "AWS_NEURON"
    vram_budget_gb: 192
    allow_cpu_fallback: false
  runtime_protection:
    enforce_compliance_lock: true
    memory_leak_threshold_mb: 1024
```

---

## 6. Running Local Conformance Tests

All unit tests and mocked hardware simulations run without physical AWS Neuron devices:

```bash
python -m pytest tests/accelerators/test_aws_neuron_backend.py -v
```
