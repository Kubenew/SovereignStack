# OASA Core Controls Matrix (CCM)

**Version:** 2026.1
**Classification:** Public Infrastructure Standard
**Framework Status:** Authoritative Audit Reference

This document defines the binding compliance framework for the OASA (Open Architecture Specification for Autonomous and Sovereign AI) standard. It serves as the official technical and operational benchmark for enterprise auditors, CISOs, and automated vulnerability scanners (`validate_compliance.py --audit-host`) verifying the security boundaries of Sovereign Nodes.

## 1. Compliance Levels

OASA certification is structured into three cumulative assurance tiers based on operational isolation and data classification risk:

- **Level 1 (Sovereign-Ready)** — Standard Enterprise Tier. Static configuration validation, basic Kubernetes container isolation, and absolute elimination of public cloud data harvesting (GDPR/CCPA compliance).
- **Level 2 (Secure-Runtime)** — Advanced Corporate Tier. Continuous process supervision, active memory drift monitoring, local KV-cache leak protection, and automated volatile memory encryption.
- **Level 3 (Strict-Sovereign)** — Government, Defense, and Financial Tier. Pure hardware-rooted identity, 100% physical air-gap isolation completely devoid of WAN interfaces, asymmetric encryption keys cryptographically bound to an on-premise TPM 2.0 / HSM module, and immutable logging.

## 2. Controls Matrix

### Section A: Network Isolation & Exfiltration (NET)

| ID | Control Description | Level | Verification Method | Reference Component |
|----|--------------------|-------|--------------------|---------------------|
| NET-01 | The Node configuration explicitly denies outbound WAN traffic (Egress) to the public internet. | L1 | Static inspection of JSON/YAML schemas; structural validation of cluster ingress/egress. | `sovereign-network-policy.yaml` |
| NET-02 | An active network probe simulating an outbound connection to an external DNS/IP (e.g., 1.1.1.1:53) terminates with a hard connection timeout. | L2 | Automated live socket probing via the `--audit-host` execution argument. | `tools/validate_compliance.py` |
| NET-03 | Node name resolution architecture is strictly forced to LOCAL_ONLY. No external upstream WAN DNS servers are active. | L3 | Inspection of localized CoreDNS upstream routing inside the air-gapped private cloud container cluster. | `privatecloud-k8s` |

### Section B: Execution Safety & Memory Protection (RUN)

| ID | Control Description | Level | Verification Method | Reference Component |
|----|--------------------|-------|--------------------|---------------------|
| RUN-01 | The active AI model execution process is sandboxed inside a protective wrapper daemon monitoring real-time RAM/VRAM resource consumption. | L2 | Dynamic confirmation that the cognitive backend is executed as a child process under the telemetry engine. | `tools/runtime_shield.py` |
| RUN-02 | If the real-time memory leak drift exceeds a defined threshold (e.g., >512 MB), the supervisor process triggers an immediate termination (Kill Switch). | L2 | Controlled simulated injection of memory space abnormalities; verify immediate processing termination. | `tools/runtime_shield.py` |
| RUN-03 | Activating `oasa_compliance_lock` ensures that under structural failure, any fallback to public cloud APIs is physically blocked. System returns a 503 code. | L3 | Simulated fault injection of local inference layer; verify reverse-proxy drops connections instead of WAN routing. | `turboprivate-ai-proxy` |

### Section C: Hardware & Cryptographic Integrity (HW)

| ID | Control Description | Level | Verification Method | Reference Component |
|----|--------------------|-------|--------------------|---------------------|
| HW-01 | All temporary storage, structured context embeddings, and active model KV-caches are processed exclusively within ephemeral volatile RAM. | L1 | Verification of Kubernetes deployment configuration ensuring `emptyDir.medium: Memory` is active. | `sovereign-deployment.yaml` |
| HW-02 | The underlying host architecture contains a fully operational, initialized physical Trusted Platform Module (TPM 2.0) or equivalent HSM. | L2 | System interrogation of `/dev/tpm0` (Linux) or structured WMI security namespace queries (Windows). | `tools/validate_compliance.py` |
| HW-03 | Cryptographic keys safeguarding data at-rest and in-transit (AES-256-GCM) are locked to the non-exportable hardware identity of the TPM 2.0 module. | L3 | Review of key management architecture; verify encryption keys are computationally inaccessible outside the local host motherboard. | `privatecloud / TPM Layer` |

### Section D: Ingestion Pipeline & Audit Logs (AUD)

| ID | Control Description | Level | Verification Method | Reference Component |
|----|--------------------|-------|--------------------|---------------------|
| AUD-01 | Incoming unstructured assets (PDF/TIFF) are cleaned, formatted, and strictly structural-validated against a JSON schema before LLM intake. | L1 | Verification of input stream logs; checking rejection rate of invalid schemas. | `pdf2struct` |
| AUD-02 | The node outputs complete, machine-readable audit trails for every API call transaction in a unified structured JSON streaming format. | L1 | Interrogation of the stdout/stderr data streams; checking for presence of mandatory compliance metadata. | SovereignStack Core |
| AUD-03 | Transaction logs are pushed directly into an immutable local data sync block with modify-protection and a minimum retention cap of 365 days. | L3 | Attempted alteration/deletion of historical indices under root privileges is rejected by the kernel filesystem architecture. | `audit.immutable: true` |

## 3. Audit Execution & Certification Workflow

```
[ STEP 1: Static Validation ]   ->   [ STEP 2: Live Host Probe ]   ->   [ STEP 3: Cryptographic Sign ]
 Verify `sovereign-stack.yaml`       Execute `validate_compliance.py`     Generate a signed audit JSON
 against OASA JSON Schemas.          with the `--audit-host` flag.         and append to public registry.
```

- **Preparation Phase:** The compliance candidate structures their deployment topology using the COMPLIANT_TEMPLATE generated via `python validate_compliance.py --generate-template`.
- **Inspection Phase:** An authorized OASA auditor (or a locked corporate CI/CD production pipeline) executes the full suite of diagnostic checks defined in this matrix.
- **Issuance Phase:** If the architecture completely satisfies every control check up to the targeted tier (e.g., all NET, RUN, and HW targets for Tier 2), the auditor cryptographically signs the generated JSON audit report. The entity is then granted the right to display the official OASA Certified - Level [1/2/3] trust badge.

## 4. Framework Cross-References

Each OASA CCM control maps to multiple industry compliance frameworks. See the dedicated mapping documents for full details.

| Framework | Mapping Document | Tiers Covered | Key Standard |
|-----------|-----------------|---------------|-------------|
| **SOC 2** | [SOC 2 Mapping](soc2-mapping.md) | L1–L3 | AICPA TSC 2023 |
| **Gaia-X** | [Gaia-X Mapping](gaia-x-mapping.md) | L1–L3 | Gaia-X Trust Framework 24.04 |
| **ISO 42001** | (Planned) | L2–L3 | AI Management System |
| **EU AI Act** | (Planned) | L2–L3 | Risk-based AI regulation |
| **NIS2** | (Planned) | L1–L3 | Network security directive |

### Quick Reference: SOC 2

| OASA Control | SOC 2 Criterion | Category |
|-------------|-----------------|----------|
| NET-01 | CC6.1, CC6.7 | Security, Confidentiality |
| NET-02 | CC6.8 | Security |
| NET-03 | CC6.1 | Security |
| RUN-01 | CC7.1, A1.2 | Security, Availability |
| RUN-02 | CC7.4, A1.3 | Security, Availability |
| RUN-03 | A1.2 | Availability |
| HW-01 | CC6.7, PI1.1 | Confidentiality, Processing Integrity |
| HW-02 | CC6.3 | Security |
| HW-03 | CC6.7 | Confidentiality |
| AUD-01 | PI1.1, CC7.2 | Processing Integrity, Security |
| AUD-02 | CC7.2, A1.2 | Security, Availability |
| AUD-03 | CC6.1 | Security |

### Quick Reference: Gaia-X

| OASA Control | Gaia-X Criterion | Category |
|-------------|------------------|----------|
| NET-01 | Data Sovereignty | Resource location enforcement |
| NET-02 | Security | Connectivity verification |
| NET-03 | Data Sovereignty | Jurisdiction-aware DNS |
| RUN-01 | Security | Workload monitoring |
| RUN-02 | Transparency | Failure observability |
| RUN-03 | Data Sovereignty | Data ecosystem confinement |
| HW-01 | Security, Data Sovereignty | Temporary storage control |
| HW-02 | Identity, Security | Hardware-anchored identity |
| HW-03 | Data Sovereignty | Owner-controlled encryption |
| AUD-01 | Transparency | Processing auditability |
| AUD-02 | Transparency | Operational observability |
| AUD-03 | Transparency | Tamper-proof audit |

## 5. Executive Impact

By checking this matrix into your SovereignStack codebase, you provide enterprise decision-makers with a highly scannable, practical template that shifts their operations from open-source experimentation to standardized risk mitigation. Corporate governance boards can immediately take this matrix, hand it to their internal IT security teams, and map out an explicit path toward air-gapped data compliance.

Your repository is now completely rounded out across economic, technical, structural, and regulatory vectors.
