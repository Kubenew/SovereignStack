# SOC 2 Trust Services Criteria — OASA CCM Mapping

**Version:** 2026.1 | **Status:** Draft
**Purpose:** Maps each OASA CCM control to the applicable SOC 2 Trust Services Criteria (TSC) categories — Security, Availability, Processing Integrity, Confidentiality, Privacy.

## Control-to-SOC 2 Mapping

| OASA Control | SOC 2 Category | SOC 2 Criterion | Mapping Rationale |
|-------------|----------------|-----------------|-------------------|
| NET-01 | Security | CC6.1 — Network segmentation | Denying outbound WAN egress is a fundamental network segmentation control |
| NET-01 | Confidentiality | CC6.7 — Protection of confidential information | Prevents data exfiltration via egress channels |
| NET-02 | Security | CC6.8 — Malicious code prevention | Active probing detects unauthorized egress attempts |
| NET-03 | Security | CC6.1 — Logical access controls | LOCAL_ONLY DNS prevents DNS-based data exfiltration |
| RUN-01 | Security | CC7.1 — System monitoring | Runtime shield provides continuous monitoring of model execution |
| RUN-01 | Availability | A1.2 — Monitoring of capacity | RAM/VRAM monitoring feeds capacity management |
| RUN-02 | Security | CC7.4 — Incident response | Kill switch is an automated incident response action |
| RUN-02 | Availability | A1.3 — Recovery from disruption | Memory drift detection triggers automated recovery |
| RUN-03 | Availability | A1.2 — Processing continuity | Compliance lock prevents fallback to unsecured cloud |
| HW-01 | Confidentiality | CC6.7 — Protection of confidential information | Ephemeral RAM ensures no persistent confidential data |
| HW-01 | Processing Integrity | PI1.1 — Complete and accurate processing | Volatile-only KV caches prevent stale-state processing errors |
| HW-02 | Security | CC6.3 — Cryptographic key management | TPM 2.0 provides hardware-rooted key protection |
| HW-03 | Confidentiality | CC6.7 — Encryption of data at rest/in transit | AES-256-GCM keys bound to TPM non-exportable identity |
| AUD-01 | Processing Integrity | PI1.1 — Complete and accurate processing | Schema validation ensures input data integrity |
| AUD-01 | Security | CC7.2 — Monitoring of logical access | Input validation prevents malformed-data attacks |
| AUD-02 | Security | CC7.2 — Audit logging | Machine-readable audit trails satisfy logging requirements |
| AUD-02 | Availability | A1.2 — Monitoring of processing | Audit stream enables real-time monitoring of system health |
| AUD-03 | Security | CC6.1 — Protection of audit logs | Immutable storage with 365-day retention prevents log tampering |

## SOC 2 Criteria Coverage Summary

| SOC 2 Category | OASA Controls Mapped | Coverage |
|----------------|---------------------|----------|
| **Security** | NET-01, NET-02, NET-03, RUN-01, RUN-02, HW-02, AUD-01, AUD-02, AUD-03 | 9 controls |
| **Availability** | RUN-01, RUN-02, RUN-03, AUD-02 | 4 controls |
| **Processing Integrity** | HW-01, AUD-01 | 2 controls |
| **Confidentiality** | NET-01, HW-01, HW-03 | 3 controls |
| **Privacy** | (Covered by jurisdiction enforcement — RFC-0021) | Implicit |

## Evidence Required for SOC 2

| SOC 2 Criterion | Evidence Artifact | OASA Schema Path |
|-----------------|-------------------|------------------|
| CC6.1 | Network policy YAML showing egress deny | `network.allow_wan: false` |
| CC6.3 | TPM attestation report | `hardware_security.tpm_version: "2.0"` |
| CC6.7 | Encryption configuration | `encryption.algorithm + key_management` |
| CC7.1 | Runtime shield logs | `tools/runtime_shield.py` output |
| CC7.2 | Audit stream sample | `audit.enabled: true, audit.log_format: "JSON"` |
| CC7.4 | Kill switch test results | `tools/runtime_shield.py` injection test |
| A1.2 | Capacity monitoring config | `compute.vram_budget_gb` + runtime logs |
| A1.3 | Recovery procedure documentation | RUN-02 verification results |
| PI1.1 | Input validation schema | `ingestion.supported_formats` + validation logs |

## Mapping Notes

- All 12 OASA CCM controls map to at least one SOC 2 TSC criterion
- **L1** (Sovereign-Ready) satisfies the majority of Security and Confidentiality criteria
- **L2** (Secure-Runtime) adds Availability and Processing Integrity coverage
- **L3** (Strict-Sovereign) satisfies all five SOC 2 categories at the highest assurance level
- SOC 2 auditors can use the `oasa-audit report` command (RFC-0040) to generate evidence packages

## References

- [OASA CCM](oasa-ccm.md) — Core Controls Matrix
- [OASA Audit Evidence Schema](../schemas/oasa-audit-evidence.schema.json)
- [RFC-0021 Jurisdiction & Data Residency](../rfcs/RFC-0021-jurisdiction-data-residency.md)
- AICPA Trust Services Criteria (TSC) 2023
