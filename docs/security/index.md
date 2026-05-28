# Security Overview

SovereignStack follows a **defense-in-depth** security model across three identity layers (user, workload, node), encrypted communication and storage, policy enforcement, and continuous monitoring.

---

## Trust Model

```
┌──────────────────────────────────────────────────────────────────┐
│                      TRUST PYRAMID                                 │
│                                                                   │
│                    ┌─────────────────────┐                        │
│                    │   ROOT OF TRUST      │                        │
│                    │  Offline HSM / CA    │                        │
│                    └──────────┬──────────┘                        │
│                               │                                    │
│                    ┌──────────▼──────────┐                        │
│                    │   NODE IDENTITY      │                        │
│                    │  Ed25519 + TPM 2.0   │                        │
│                    │  RFC 0003            │                        │
│                    └──────────┬──────────┘                        │
│                               │                                    │
│                    ┌──────────▼──────────┐                        │
│                    │  WORKLOAD IDENTITY   │                        │
│                    │  SPIFFE / SPIRE      │                        │
│                    │  SVID (X.509/JWT)    │                        │
│                    └──────────┬──────────┘                        │
│                               │                                    │
│                    ┌──────────▼──────────┐                        │
│                    │   USER IDENTITY      │                        │
│                    │  Keycloak OIDC       │                        │
│                    │  RBAC (3 roles)      │                        │
│                    └─────────────────────┘                        │
└──────────────────────────────────────────────────────────────────┘
```

### Identity Layers

| Layer | Identity | Mechanism | Purpose |
|---|---|---|---|
| **Node** | `eu-fr1-a7f3...` | Ed25519 key, TPM AIK, X.509 cert | Mesh authentication, audit attribution |
| **Workload** | `spiffe://sovereign.stack/service/gateway` | SPIRE-issued SVID (X.509/JWT) | Inter-service mTLS, audit enrichment |
| **User** | `user:analyst` | Keycloak OIDC JWT | API authentication, RBAC authorization |

---

## Security Controls by Layer

### 1. Network

| Control | Implementation |
|---|---|
| Transport encryption | TLS 1.3 (external), WireGuard (mesh) |
| Network isolation | Internal-only bridge (`sovereign-isolated-net`) |
| Egress filtering | Default-deny; documented in `sovereign-stack.yaml` |
| Service discovery | Internal DNS in bridge network |

### 2. Authentication & Authorization

| Control | Implementation |
|---|---|
| User auth | OIDC JWT (RS256/RS384/RS512) via Keycloak |
| RBAC | 3 roles: `inference:write`, `inference:read`, `audit:read` |
| Workload auth | SPIFFE X.509 SVIDs for inter-service mTLS |
| Node auth | Ed25519 signatures + TPM 2.0 attestation |
| Guest/fallback tokens | `mock-valid-token` in dev mode only |

### 3. Data at Rest

| Control | Implementation |
|---|---|
| Encryption | AES-256-GCM per document |
| Key management | TPM 2.0 wrapping (hardware) or key file (software) |
| Key rotation | On node re-provisioning (key bound to node identity) |

### 4. Data in Transit

| Control | Implementation |
|---|---|
| External API | TLS 1.3 (HTTPS) |
| Internal services | TLS within Docker bridge network |
| Mesh federation | WireGuard (ChaCha20-Poly1305) |

### 5. Compute Isolation

| Control | Implementation |
|---|---|
| Sandbox | gVisor (Kubernetes) / container isolation (Docker) |
| GPU isolation | vLLM PagedAttention per-request VRAM isolation |
| Code execution | No arbitrary code execution in gateway |
| Resource limits | cgroup CPU/memory limits on all containers |

### 6. Audit & Monitoring

| Control | Implementation |
|---|---|
| Audit log | Append-only JSON, all requests/responses logged |
| Alerting | 21 Prometheus alerts (gateway, vLLM, memory, ingest, SPIRE) |
| Node health | HTTP health checks on all services |
| Threat detection | Auth failure rate, compliance violation rate, policy block rate |

---

## Key Security Documents

| Document | Contents |
|---|---|
| [Threat Model](/docs/security/threat-model.md) | 53 STRIDE threats, 8 trust zones, risk register |
| [SPIFFE Integration](/docs/security/spiffe.md) | SPIRE architecture, workload attestation, SVID lifecycle |
| [Compliance Framework](/docs/compliance/index.md) | GDPR, HIPAA, SOC 2 control mapping |
| [SECURITY.md](/SECURITY.md) | Vulnerability disclosure policy, bounty program |

---

## Incident Response

| Phase | Actions | Automation |
|---|---|---|
| **Detect** | Alert fires (Prometheus `Warning`/`Critical`) | Pager notification via Alertmanager |
| **Triage** | Check audit log for anomalous events | `GET /events?actor=<x>&since=<time>` |
| **Contain** | Revoke node cert or user token | Keycloak admin / SPIRE entry update |
| **Eradicate** | Rotate keys, patch vulnerability | TPM re-key, container image rebuild |
| **Recover** | Restore from backup | `POST /memory/backup`, Longhorn snapshot |
| **Post-mortem** | Update threat model, add test case | PR with new CI conformance test |

---

## Security Configuration

```yaml
security:
  auth:
    oidc_issuer: "http://keycloak:8083/realms/sovereign"
    oidc_client_id: "sovereign-gateway"
    enforce_auth: "STRICT"
  policy:
    engine: "opa"
    enforce_policy: "STRICT"
  encryption:
    algorithm: "AES-256-GCM"
    tpm_binding: true
  monitoring:
    alerts: "config/prometheus-alerts.yml"
    audit_log: "data/audit.log"
  identity:
    node: "ed25519 + tpm2"
    workload: "spiffe"
```

---

## See Also

- [Security Threat Model (53 STRIDE threats)](/docs/security/threat-model.md)
- [SPIFFE / SPIRE Workload Identity](/docs/security/spiffe.md)
- [Compliance Framework (GDPR / HIPAA / SOC 2)](/docs/compliance/index.md)
- [Networking Mesh](/docs/networking/index.md)
- [SECURITY.md (vulnerability disclosure)](/SECURITY.md)
