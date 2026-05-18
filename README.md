# SovereignStack — OASA Specification

**Open Architecture Specification for Autonomous and Sovereign AI (OASA)**  
Version: **2026.1**  
Status: **Architecture Blueprint**  
Target: **Local-First, Air-Gapped, High-Efficiency Enterprise AI Infrastructure**

[![Schema Validation](https://github.com/Kubenew/SovereignStack/actions/workflows/validate.yml/badge.svg)](https://github.com/Kubenew/SovereignStack/actions/workflows/validate.yml)

---

This repository contains the **OASA specification**, defining an open standard for building sovereign AI infrastructure using the [Kubenew](https://github.com/Kubenew) ecosystem:

| Component | Role |
|---|---|
| **[privatecloud](https://github.com/Kubenew/privatecloud)** | Sovereign orchestration / air-gapped K8s appliance |
| **[TurboQuant-v3](https://github.com/Kubenew/TurboQuant-v3)** | Execution optimization / quantization runtime |
| **[turboprivate-ai](https://github.com/Kubenew/turboprivate-ai)** | Enterprise LLM gateway + policy engine |
| **[pdf2struct](https://github.com/Kubenew/pdf2struct)** | Deterministic ingestion of unstructured documents |
| **[TurboMemory](https://github.com/Kubenew/TurboMemory)** | Local memory & vector isolation |

---

## Repository Contents

```
SovereignStack/
├── OASA.md                                  # Full specification document
├── CONTRIBUTING.md                          # How to contribute
├── LICENSE                                  # Apache-2.0
├── schemas/
│   ├── oasa-compliance.schema.json          # Node compliance configuration
│   ├── oasa-node-manifest.schema.json       # Sovereign Node inventory & status
│   └── oasa-request.schema.json             # OpenAI-compatible request format
├── examples/
│   ├── openai_proxy_request.sh              # Bash — curl examples
│   ├── openai_proxy_request.py              # Python — SDK & requests examples
│   └── sample_compliance.json               # Fully compliant reference config
├── tools/
│   ├── validate_compliance.py               # Schema validator CLI
│   └── requirements.txt                     # Python dependencies
└── .github/
    └── workflows/
        └── validate.yml                     # CI — schema & syntax validation
```

---

## Purpose

OASA defines an architectural framework where **computation and cognitive memory remain bound to the physical geography of the asset owner**.

It rejects the thin-client SaaS model and instead mandates the **Sovereign Node topology**, preventing exfiltration of prompts, embeddings, telemetry, and confidential enterprise data.

---

## The Three Axioms

1. **Zero Exfiltration** — No data leaves the node without cryptographically signed consent.
2. **Hardware Agnosticism** — Run on commodity hardware via aggressive quantization (FP16 → INT4/INT2).
3. **API Idempotency** — Drop-in replacement for OpenAI APIs. Zero code changes required.

---

## The Four Layers

```
┌──────────────────────────────────────────────┐
│  1. OASA-Ingest   (pdf2struct)               │
│     Deterministic document extraction        │
├──────────────────────────────────────────────┤
│  2. OASA-Memory   (TurboMemory)              │
│     Encrypted vector store + KV cache        │
├──────────────────────────────────────────────┤
│  3. OASA-Compute  (TurboQuant + turboprivate)│
│     Adaptive quantized execution             │
├──────────────────────────────────────────────┤
│  4. OASA-Node     (privatecloud)             │
│     Air-gapped K8s orchestration             │
└──────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Drop-In API Migration

```bash
export OPENAI_BASE_URL="http://localhost:8080/v1"
export OASA_ENFORCE_COMPLIANCE="STRICT"
```

Existing LangChain, AutoGPT, or internal tools work immediately.

### 2. Validate Your Configuration

```bash
pip install -r tools/requirements.txt

# Validate a config
python tools/validate_compliance.py examples/sample_compliance.json

# Generate a compliant template
python tools/validate_compliance.py --generate-template > my-config.json
```

### 3. Try the Examples

```bash
# Bash
bash examples/openai_proxy_request.sh

# Python (uses openai SDK or plain requests)
python examples/openai_proxy_request.py
```

---

## Compliance Positioning

When compliance asks:

> "Are we exposed to GDPR/HIPAA/financial risk by using AI?"

The answer becomes:

> "Not if we comply with OASA."

| Regulation | OASA Coverage |
|---|---|
| GDPR (EU) | Zero Exfiltration, jurisdiction routing, audit logs |
| HIPAA (US) | Encryption at rest, air-gapped compute, access logging |
| NIS2 (EU) | Hardware security modules, immutable audit trail |
| SOX (US) | Deterministic ingestion, tamper-evident logs |
| DORA (EU) | Operational resilience via air-gapped orchestration |

---

## Schemas

| Schema | Purpose |
|---|---|
| [`oasa-compliance.schema.json`](schemas/oasa-compliance.schema.json) | Full node compliance configuration |
| [`oasa-node-manifest.schema.json`](schemas/oasa-node-manifest.schema.json) | Node identity, hardware, deployed models |
| [`oasa-request.schema.json`](schemas/oasa-request.schema.json) | OASA-extended OpenAI request format |

All schemas follow **JSON Schema Draft 2020-12** with full descriptions, enums, and examples.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on spec changes, schema contributions, and coding style.

---

## License

Apache-2.0 — see [LICENSE](LICENSE).
