# SovereignStack (OASA Reference Implementation)

[![OASA Compliance: Strict](https://shields.io)](#compliance)
[![Infrastructure: Air-Gapped](https://shields.io)](#architecture)
[![License: Apache 2.0](https://shields.io)](LICENSE)

**SovereignStack** is a complete, production-ready open-source infrastructure blueprint for executing local, highly optimized, and entirely air-gapped Large Language Models (LLMs). Implementing the **OASA** (Open Architecture Specification for Autonomous and Sovereign AI) standard, this stack unifies unstructured data pipeline ingestion, advanced quantization layers, and private cloud orchestration.

By moving your architecture to SovereignStack, you transition away from the speculative subscription model of cloud rental ($Д - Д'$) and return to a stable, value-generating corporate capital asset workflow ($Д - Т - Д'$), where you maintain absolute ownership of your data, models, and physical compute.

---

## 🏛️ Ecosystem Architecture & Interconnectivity

SovereignStack unifies fragmented open-source software layers into a single, cohesive enterprise appliance:

```
┌─────────────────────────────────────────────────────────┐
│                 1. INGESTION LAYER                      │
│    (pdf2struct: Volatile In-Memory PDF-to-JSON Pipeline)│
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  2. COGNITIVE MEMORY                    │
│     (TurboMemory: Isolated Local Vector Context Layer)  │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 3. COMPUTE & OPTIMIZATION               │
│    (TurboQuant-v3 + turboprivate-ai: INT4 AWQ Core)     │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│               4. SOVEREIGN ORCHESTRATION                │
│  (privatecloud: Air-Gapped K8s Runtime Guard Engine)    │
└─────────────────────────────────────────────────────────┘
```

1. **OASA-Ingest (`pdf2struct`)**: Automatically processes unstructured PDFs, TIFFs, and documents inside volatile memory (RAM), enforcing zero temporary cache footprint on unencrypted physical disks.
2. **OASA-Memory (`TurboMemory`)**: Isolates context and handles local vector retrieval loops, encrypting embedding databases at rest via AES-256-GCM bound to a hardware TPM 2.0 module.
3. **OASA-Compute (`TurboQuant-v3` & `turboprivate-ai`)**: Executes ultra-compressed mixed-precision models (INT4/AWQ), slashing corporate hardware overhead by 80% and allowing 72B parameter models to run locally on a single 24GB VRAM GPU instead of massive cloud arrays.
4. **OASA-Node (`privatecloud`)**: The underlying secure Kubernetes container cluster fabric, enforcing strict traffic segmentation, automated memory isolation, and host integrity verification.

---

## 🛡️ Built for Enterprise Compliance (CISO / Legal)

SovereignStack treats security not as an afterthought, but as an absolute infrastructure primitive designed to meet the world's most demanding regulatory matrices:

| Regulation | Public Cloud AI Risks | SovereignStack Mitigation Strategy |
| :--- | :--- | :--- |
| **GDPR / CCPA** | Critical leak of Personally Identifiable Information (PII) to third-party providers (OpenAI/Anthropic APIs) for model training. | **100% Air-Gap Execution.** Data never leaves the geographic perimeter of your hardware node. Network layers actively terminate WAN leaks. |
| **HIPAA** | Unintentional exposure of Protected Health Information (PHI) to remote cloud mirrors. | Volatile-only pipeline ingestion. Local vector memory is bound directly to hardware-rooted encryption keys inside the physical **TPM 2.0** chip. |
| **DORA / NIS2** | Complete operational paralysis during public cloud outages and systemic vendor lock-in. | **Total Architectural Autonomy.** If external network links or tier-1 hyperscalers crash, the local AI infrastructure continues running uninterrupted. |

---

## ⚡ Quick Start

### 1. Clone the Stack and Submodules
```bash
git clone --recursive https://github.com/Kubenew/SovereignStack.git
cd SovereignStack
pip install -r tools/requirements.txt
```

### 2. Run Pre-Flight Compliance & Infrastructure Auditing
Before spinning up the containers, use the validator tool. Passing the `--audit-host` flag transitions the script from a passive JSON validator into an active systems auditor—interrogating `nvidia-smi` for VRAM capacity, detecting hardware TPM chips, and executing low-level network socket probes to verify the air-gap:

```bash
python tools/sovereign_stack.py validate sovereign-stack.yaml --audit-host
```

### 3. Launch the Stack via the Runtime Shield Wrapper
To secure model inference, execution is wrapped by `runtime_shield.py`. This daemon acts as a physical watchdog, monitoring real-time RAM/VRAM drift caused by KV-cache anomalies and instantly killing the core process via an immutable `Kill Switch` if a network leak or threshold breach is detected:

```bash
python tools/runtime_shield.py \
  --config sovereign-stack.yaml \
  --cmd "python3 -m turboprivate_ai.main --port 8080"
```

### 4. Deploy Native Kubernetes Manifests
Instantly bootstrap your `privatecloud` container architecture by applying the declarative configurations to your internal bare-metal cluster:

```bash
kubectl apply -f k8s/sovereign-network-policy.yaml
kubectl apply -f k8s/sovereign-configmap.yaml
kubectl apply -f k8s/sovereign-deployment.yaml
kubectl apply -f k8s/sovereign-service.yaml
```

---

## 🔄 Seamless Drop-in Enterprise Workflow Integration

SovereignStack exposes a local reverse proxy proxying an API schema that is 100% identical to the OpenAI REST specification. To migrate your corporate applications, autonomous agents, LangChain wrappers, or workflows away from cloud monopolies, swap exactly **one line of code** in your infrastructure environment configuration:

```bash
export OPENAI_BASE_URL="http://cluster.local"
export OASA_ENFORCE_COMPLIANCE="STRICT"
```

---

## 🛠️ Infrastructure Roadmap

- [x] Establish core OASA architectural specifications and JSON schema templates.
- [x] Engineer live system probing and network leakage detection inside `validate_compliance.py` / `sovereign_stack.py`.
- [x] Create active memory drift and WAN isolation enforcement wrappers via `runtime_shield.py`.
- [x] Build out native air-gapped Kubernetes network policies and cluster manifests for `privatecloud`.
- [ ] Build automated internal inference throughput (Tokens/Sec) profiling against varying `TurboQuant-v3` weights quantization bit-depths.
- [ ] Develop a centralized, air-gapped web dashboard for auditing localized enterprise carbon quotas and social token utilization policies.

---

## 📄 License

This enterprise stack is distributed under the Apache 2.0 License. Review the [LICENSE](LICENSE) manifest file for full legal terminology.

**SovereignStack — Your Code. Your Hardware. Your Sovereignty.**
