# Compliance Framework

SovereignStack provides controls and documentation to support regulatory compliance across multiple jurisdictions, including GDPR (EU), HIPAA (US), and SOC 2 (general IT controls).

---

## Compliance Matrix

| Framework | Jurisdiction | SovereignStack Controls | Certification |
|---|---|---|---|
| **GDPR** | EU | Article 5 (data minimisation), Article 17 (right to erasure), Article 32 (encryption) | Self-certified mapping |
| **HIPAA** | US | 45 CFR §164.312 (access controls, encryption, audit trails) | Self-certified mapping |
| **SOC 2** | General | TSC Category A1/C1/CC6 (encryption, access, monitoring) | Self-certified mapping |
| **CCPA** | US (California) | Data inventory, deletion API, opt-out mechanism | In progress |
| **LGPD** | Brazil | Mapping to GDPR-equivalent controls | Planned |
| **PIPEDA** | Canada | Mapping to GDPR-equivalent controls | Planned |

---

## Control Mapping

### GDPR Controls

| GDPR Article | Requirement | SovereignStack Control | Verification |
|---|---|---|---|
| Art. 5(1)(c) | Data minimisation | `oasa_compliance_lock` prevents data exfiltration | CI test `test_oasa_lock_prevents_fallback` |
| Art. 17 | Right to erasure | `DELETE /embed`, `POST /cache/clear` endpoints | API-level verification |
| Art. 25 | Data protection by design | Air-gapped mode, encryption at rest, RBAC | OASA L2 conformance |
| Art. 32 | Security of processing | AES-256-GCM, TPM binding, gVisor sandbox | Threat model §4 |
| Art. 33 | Breach notification | Audit log event stream, Prometheus `GatewayAuthFailureRate` alert | Monitoring integration |
| Art. 35 | DPIA | Threat model document, architecture review | docs/security/threat-model.md |

### HIPAA Controls

| HIPAA Rule | Requirement | SovereignStack Control | Verification |
|---|---|---|---|
| 45 CFR §164.312(a)(1) | Access control | OIDC + RBAC (3 roles: `inference:write`, `inference:read`, `audit:read`) | CI test `test_gateway_auth_strict_*` |
| 45 CFR §164.312(a)(2)(iv) | Encryption | AES-256-GCM at rest, TLS 1.3 in transit | Config verification |
| 45 CFR §164.312(b) | Audit controls | Append-only audit log with Merkle chaining | CI test `test_merkle_tree_audit_format` |
| 45 CFR §164.312(c)(1) | Integrity | Event log signatures, CRDT validation | Threat model §4 |
| 45 CFR §164.312(d) | Person authentication | OIDC JWT validation with JWKS + SPIFFE workload identity | CI test `test_gateway_auth_strict_success_token` |
| 45 CFR §164.308(a)(1) | Security management | Threat model, conformance tests, CI/CD pipeline | Threat model + CI |

### SOC 2 Controls

| TSC Category | Control | SovereignStack Control |
|---|---|---|
| **A1** (Availability) | Monitoring | Prometheus + alerting (21 rules), health checks on all services |
| **C1** (Confidentiality) | Encryption | AES-256-GCM at rest, TLS 1.3 in transit, TPM key binding |
| **CC6** (Logical Access) | Access control | OIDC authentication, RBAC authorization, SPIFFE workload identity |

---

## Conformance Levels

OASA defines three conformance levels, each with an associated compliance scope:

| Level | Compliance Scope | Verification |
|---|---|---|
| **L1 — Compatible** | Basic controls | CI validation, schema checks |
| **L2 — Verified** | GDPR Art. 32, HIPAA 164.312, SOC 2 CC6 | Conformance tests, encryption verification |
| **L3 — Certified** | Full compliance mapping | Third-party audit (planned) |

```bash
# Generate compliance report
python tools/generate_compliance_report.py --level L2 --output reports/compliance-report.md

# Run conformance tests
python -m pytest tests/conformance/ -v --level L2
```

---

## Data Flow & Residency

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Client     │───►│  Gateway    │───►│  Memory     │
│  EU region  │    │  EU node    │    │  (local)    │
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
                   ┌──────▼──────┐
                   │  Audit Log  │
                   │  (EU-local) │
                   └─────────────┘
```

| Stage | Data | Jurisdiction | Control |
|---|---|---|---|
| Client → Gateway | Prompt text | Client region | TLS 1.3 |
| Gateway → Compute | Processed prompt | Node region | gVisor isolation |
| Gateway → Memory | Embeddings | Node region | AES-256-GCM at rest |
| Audit log | Full request/response | Node region | Append-only, immutable |
| Federation sync | Metadata only | Same-jurisdiction only | Jurisdictional gating |

---

## Audit Evidence

The following artifacts support compliance audits:

| Artifact | Location | Contents |
|---|---|---|
| Audit log | `data/audit.log` + Merkle tree `data/merkle_tree.json` | All inference requests/responses with timestamps, SHA-256 hashed into append-only Merkle tree |
| Merkle root | `GET /audit/root` | Current root hash = cryptographic fingerprint of entire audit log |
| Compliance report | `reports/l2-report.md` | Control-by-control verification |
| Threat model | `docs/security/threat-model.md` | STRIDE analysis, risk register |
| Conformance test results | CI pipeline | JUnit XML with pass/fail per test |
| SBOM | `reports/sovereignstack-sbom.*` | CycloneDX + SPDX dependency inventory |
| Node identity | `GET /identity` | Signed node identity document |
| Workload identity | `GET /spiffe` | SPIFFE SVID for running services |

---

## Data Retention & Deletion

| Data Type | Retention | Deletion Method |
|---|---|---|
| Vector embeddings | Configurable (default: indefinite) | `DELETE /embed/{doc_id}` |
| KV cache entries | TTL-based (default: 1h) | Automatic expiry + `POST /cache/clear` |
| Audit log entries | Configurable (default: 90 days) | Rotation with archival |
| Inference logs | Not stored beyond audit log | N/A (transient) |

---

## Regional Configuration

```yaml
compliance:
  jurisdiction: "EU"
  frameworks:
    - "GDPR"
  data_residency: "strict"        # Block cross-border sync
  audit_retention_days: 90
  encryption_standard: "AES-256-GCM"
  breach_notification:
    enabled: true
    webhook: "https://security-team/webhook/breach"
```

---

## Third-Party Certifications

| Certification | Status | Target |
|---|---|---|
| SOC 2 Type II | Planned | Q4 2026 |
| ISO 27001 | Planned | 2027 H1 |
| FedRAMP | Exploratory | 2027 H2 |

---

## See Also

- [Security Threat Model](/docs/security/threat-model.md)
- [SPIFFE / SPIRE Integration](/docs/security/spiffe.md)
- [Deployment Profiles](/docs/deployment/profiles.md)
- [OASA Conformance Tests](/tests/conformance/)
- [RFC 0006: Memory Specification](/rfcs/0006-memory-spec.md)
