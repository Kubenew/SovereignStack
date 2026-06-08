# Gaia-X Trust Framework — OASA CCM Mapping

**Version:** 2026.1 | **Status:** Draft
**Purpose:** Maps each OASA CCM control to the Gaia-X Trust Framework criteria — Identity, Security, Data Sovereignty, Transparency, Portability, Interoperability.

## Control-to-Gaia-X Mapping

| OASA Control | Gaia-X Criterion | Gaia-X Requirement | Mapping Rationale |
|-------------|-----------------|--------------------|-------------------|
| NET-01 | Data Sovereignty | Resource must enforce data location constraints | Egress denial prevents data leaving sovereign boundary |
| NET-02 | Security | Connectivity must be verifiable | Active probing validates network isolation compliance |
| NET-03 | Data Sovereignty | DNS resolution must be jurisdiction-aware | LOCAL_ONLY DNS prevents jurisdiction-leaking DNS queries |
| RUN-01 | Security | Workload execution must be monitored | Runtime shield provides execution transparency |
| RUN-02 | Transparency | Failures must be observable | Kill switch events are observable system behaviors |
| RUN-03 | Data Sovereignty | Data processing must not leave ecosystem | Compliance lock prevents cloud fallback exfiltration |
| HW-01 | Data Sovereignty | Data must be deletable | Ephemeral RAM ensures data is fully cleared |
| HW-01 | Security | Temporary storage must be controlled | `emptyDir.medium: Memory` ensures volatile-only storage |
| HW-02 | Identity | Participant must have verifiable identity | TPM provides hardware-anchored identity |
| HW-02 | Security | Cryptographic keys must be hardware-protected | TPM 2.0 / HSM satisfies key protection requirements |
| HW-03 | Data Sovereignty | Encryption keys must be under data owner control | Non-exportable TPM-bound keys ensure owner-only access |
| AUD-01 | Transparency | Data processing must be auditable | Input validation produces auditable processing records |
| AUD-02 | Transparency | Operations must be observable | Real-time audit stream provides operational transparency |
| AUD-03 | Transparency | Audit logs must be tamper-proof | Immutable logs satisfy Gaia-X audit integrity requirements |

## Gaia-X Self-Description Mapping

Gaia-X requires each participant/node to publish a **Self-Description** document. The OASA compliance schema maps as follows:

| Gaia-X Self-Description Field | OASA Config Path | Example Value |
|------------------------------|-----------------|---------------|
| `participant.legalName` | Node operator metadata | `"SovereignStack Inc."` |
| `participant.jurisdiction` | `jurisdiction.declared` | `"EU"` |
| `service.region` | `network.allowed_egress_cidrs` | `["10.0.0.0/8"]` |
| `service.dataProtection` | `encryption.algorithm` + `key_management` | `"AES-256-GCM"`, `"TPM_2.0"` |
| `service.certification` | `compliance_level` | `"STRICT_L3"` |
| `service.auditLogging` | `audit.enabled` + `audit.immutable` | `true`, `true` |
| `physicalResource.tpm` | `hardware_security.tpm_version` | `"2.0"` |

## Gaia-X Criteria Coverage Summary

| Gaia-X Criterion | OASA Controls Mapped | Coverage |
|-----------------|---------------------|----------|
| **Identity** | HW-02 | 1 control |
| **Security** | NET-02, RUN-01, HW-01, HW-02 | 4 controls |
| **Data Sovereignty** | NET-01, NET-03, RUN-03, HW-01, HW-03 | 5 controls |
| **Transparency** | RUN-02, AUD-01, AUD-02, AUD-03 | 4 controls |
| **Portability** | (Covered by RFC-0001 Object Model, RFC-0025 Session Migration) | Implicit |
| **Interoperability** | (Covered by RFC-0002 URI Standard, RFC-0030 Topology Awareness) | Implicit |

## Automated Self-Description Generation

The `oasa-audit report` command (RFC-0040) can generate a Gaia-X-compatible Self-Description from the compliance config:

```bash
oasa-audit report --framework gaia-x --format self-description > gaia-x-self-description.json
```

## References

- [OASA CCM](oasa-ccm.md) — Core Controls Matrix
- [RFC-0021 Jurisdiction & Data Residency](../rfcs/RFC-0021-jurisdiction-data-residency.md)
- [OASA Audit Evidence Schema](../schemas/oasa-audit-evidence.schema.json)
- [Gaia-X Trust Framework 24.04](https://docs.gaia-x.eu/trust-framework/)
- [Gaia-X Self-Description Specification](https://docs.gaia-x.eu/self-description/)
