# OASA Conformance Test Suite & Certification Program

**Version:** 2026.1  
**Status:** Specification v1  
**License:** Apache-2.0

---

## Overview

The OASA Conformance Test Suite defines a three-tier certification program for sovereign AI infrastructure. It provides automated validation, verifiable compliance proofs, and a recognized badge system — enabling enterprises to select, deploy, and audit OASA-compliant systems with confidence.

Inspired by the **Certified Kubernetes** program, **CII Best Practices Badge**, and **OpenChain** standards.

---

## Certification Levels

| Level | Name | Target Audience | Key Requirements | Badge |
|-------|------|-----------------|------------------|-------|
| **L1** | OASA Compatible | Startups, Developers, General | OpenAI-compatible API, basic validation, air-gap capable | ![OASA L1](../badges/oasa-l1.svg) |
| **L2** | OASA Verified | Mid-size Enterprises | L1 + Compliance lock, TPM 2.0 binding, volatile ingestion, audit logs | ![OASA L2](../badges/oasa-l2.svg) |
| **L3** | OASA Certified | Regulated Enterprises, Government | L2 + Merkle-tree audit, third-party review, supply chain signing, reference architecture | ![OASA L3](../badges/oasa-l3.svg) |

---

## Level 1: OASA Compatible

### Requirements

1. **OpenAI-Compatible API**
   - Must expose a `/v1/chat/completions` endpoint
   - Must support the standard OpenAI request schema
   - Must return valid completions for at least one model

2. **Basic Air-Gap Capability**
   - Must provide a configuration option to disable WAN egress
   - Must include a NetworkPolicy or firewall rule recommendation
   - Must document how to run in air-gapped mode

3. **Schema Validation**
   - Must include a valid `sovereign-stack.yaml` manifest
   - Manifest must pass validation against the official OASA JSON Schema
   - Must document the OASA version supported

4. **Documentation**
   - Must include a README with deployment instructions
   - Must document compliance mode settings
   - Must include license file (Apache 2.0 recommended)

### Automated Tests

```bash
# Schema validation
python tools/validate_compliance.py sovereign-stack.yaml

# API compatibility
python tools/benchmark.py --url http://localhost:8080/v1 --model sovereign-test-model

# Basic audit
python tools/sovereign_stack.py validate sovereign-stack.yaml
```

### Badge Usage

```markdown
![OASA Compatible](https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-compatible.svg)
```

---

## Level 2: OASA Verified

### Requirements (all L1, plus)

1. **Compliance Lock Enforcement**
   - Requests without `oasa_compliance_lock: true` must be rejected with HTTP 400/503
   - Must never fallback to external cloud APIs when lock is enabled
   - Must log every compliance violation to an immutable audit trail

2. **TPM 2.0 / Hardware Binding**
   - Must verify TPM presence on startup (Windows TPM, Linux `/dev/tpm0`)
   - Must bind encryption keys to hardware root of trust
   - Must refuse to start if required hardware security module is absent

3. **Volatile Ingestion**
   - Document processing must occur entirely in-memory
   - No temporary files written to unencrypted disk
   - Must pass the volatile ingestion test suite

4. **Audit Logging**
   - Every request must be logged with timestamp, trace ID, compliance lock status
   - Audit log must be append-only and tamper-evident
   - Retention period must be configurable (minimum 365 days recommended)

5. **Runtime Protection**
   - Must include a runtime shield (memory leak detection, network isolation monitor)
   - Must terminate inference on memory threshold breach
   - Must detect and block unauthorized network connections

### Automated Tests

```bash
# Compliance lock enforcement
python -m pytest tests/conformance/test_compliance_lock.py -v

# Runtime shield
python -m pytest tests/conformance/test_runtime_shield.py -v

# Hardware binding (simulated in CI)
python -m pytest tests/conformance/test_hardware_binding.py -v

# Audit log verification
python tools/sovereign_stack.py validate sovereign-stack.yaml --audit-host

# Full L2 suite
python -m pytest tests/conformance/ -v --level L2
```

### Badge Usage

```markdown
![OASA Verified](https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-l2.svg)
```

---

## Level 3: OASA Certified

### Requirements (all L1 + L2, plus)

1. **Immutable Merkle-Tree Audit Logs**
   - Audit log entries must be chained via cryptographic hash pointers (Merkle DAG)
   - Must support remote verification of log integrity
   - Must provide a CLI tool to verify log chains

2. **Supply Chain Security**
   - All container images must be signed with Cosign (Sigstore)
   - Must provide a Software Bill of Materials (SBOM) in SPDX or CycloneDX format
   - Model weights must be verified via SHA-256 hashes against signed manifests

3. **Independent Security Review**
   - Must have completed a third-party security audit (e.g., Trail of Bits, OpenSSF)
   - Must publish audit findings and remediation report
   - Must have a documented vulnerability disclosure process

4. **Reference Architecture**
   - Must provide a validated reference architecture for at least one hardware platform
   - Must include benchmark results (latency, throughput, VRAM utilization)
   - Must include a validated Helm chart or Terraform module

5. **Governance Compliance**
   - Must have a DCO (Developer Certificate of Origin) process
   - Must have a Code of Conduct
   - Must have at least 2 maintainers from different organizations

### Certification Process

1. **Submit** a conformance report generated by the automated test suite
2. **Provide** evidence for manual review items (security audit, SBOM, etc.)
3. **Undergo** spot-check validation by OASA Technical Steering Committee
4. **Pay** certification fee (if applicable; €500-2000 for L3 sustainability)
5. **Receive** badge + machine-readable JSON attestation + listing in OASA registry
6. **Renew** annually with re-testing

### Badge Usage

```markdown
![OASA Certified](https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-certified.svg)
```

---

## Test Suite Implementation

### Directory Structure

```
tests/conformance/
├── __init__.py
├── conftest.py              # Shared fixtures and test configuration
├── test_schema_validation.py
├── test_compliance_lock.py
├── test_runtime_shield.py
├── test_ingestion.py
├── test_hardware_binding.py
└── test_audit_log.py
```

### Running the Test Suite

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov jsonschema pyyaml

# Run all conformance tests
python -m pytest tests/conformance/ -v

# Run specific level
python -m pytest tests/conformance/ -v --level L2

# Generate report
python tools/generate_compliance_report.py --level L2 --output report.md
```

### CI Integration

A GitHub Actions workflow runs the conformance suite on every push:

```yaml
# See .github/workflows/oasa-conformance.yml
name: OASA Conformance
on: [push, pull_request]
jobs:
  conformance:
    strategy:
      matrix:
        level: [L1, L2]
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/conformance/ -v --level ${{ matrix.level }}
```

---

## Certification Schema

The machine-readable certification attestation format:

```json
{
  "oasa_version": "2026.1",
  "certification": {
    "level": "L3",
    "status": "active",
    "issued": "2026-05-25T00:00:00Z",
    "expires": "2027-05-25T00:00:00Z",
    "badge_url": "https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-l3.svg"
  },
  "subject": {
    "name": "Product/Organization Name",
    "version": "1.0.0",
    "type": "inference-engine|gateway|platform|node"
  },
  "tests": {
    "passed": 24,
    "failed": 0,
    "skipped": 0,
    "suite_version": "1.0"
  },
  "evidence": {
    "security_audit": "https://example.com/audit-2026.pdf",
    "sbom": "https://example.com/sbom.spdx.json",
    "signature": "https://example.com/certificate.pem"
  }
}
```

See [schemas/certification/oasa-certification.schema.json](../schemas/certification/oasa-certification.schema.json) for the formal JSON Schema.

---

## Public Registry

OASA-certified implementations are listed in a public registry. To add your implementation:

1. Pass the conformance test suite at your target level
2. Submit a PR to [REGISTRY.md](../REGISTRY.md) with your details
3. Provide machine-readable attestation
4. Receive your badge

---

## Compliance Mapping

| Regulation | L1 | L2 | L3 |
|------------|:--:|:--:|:--:|
| **GDPR** (EU) | Documentation | Audit logs + Access control | Immutable proofs + DPA |
| **EU AI Act** | Transparency | Risk management | Conformity assessment |
| **HIPAA** (US) | BA agreement ready | Encryption + Access logs | Audit trail + BAA |
| **DORA** (EU) | Resilience docs | Testing + Monitoring | Third-party audit |
| **NIS2** (EU) | Incident response | Supply chain security | Hardened + Certified |
| **SOX** (US) | Financial data isolation | Tamper-evident logs | External audit |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2026.1 | 2026-05-25 | Initial specification |

---

## Governance

The OASA Conformance Program is governed by the [OASA Technical Steering Committee](../GOVERNANCE.md). Changes to this specification require TSC approval.

## License

Apache 2.0
