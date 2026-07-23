# OpenID Connect Protocol Mapping

**Version:** 1.0  
**Status:** Draft  
**Related:** [ss-identity](../../ss-identity/) · [ss-economy/fin_identity](../../ss-economy/src/fin_identity.rs)

---

## Overview

[OpenID Connect (OIDC)](https://openid.net/connect/) is an identity layer on top of OAuth 2.0. SovereignStack integrates OIDC for human operator authentication, agent identity bootstrapping, and financial identity verification.

---

## Integration Points

### 1. Operator Authentication

| OIDC Concept | SovereignStack Mapping |
|---|---|
| ID Token | `operator://` identity claim |
| UserInfo endpoint | Mapped to `person://` twin attributes |
| `sub` claim | Linked to `identity://human/<sub>` |
| `aud` claim | Validated against `node://` identity |
| Scopes | Mapped to `capability://` tokens |

### 2. Agent Identity Bootstrap

| OIDC Flow | Use Case |
|---|---|
| Client Credentials | Agent-to-agent authentication (M2M) |
| Device Authorization | IoT / `robot://` device enrollment |
| Authorization Code + PKCE | Human-in-the-loop agent provisioning |

### 3. Financial Identity (KYC)

| OIDC Extension | SovereignStack Mapping |
|---|---|
| `eKYC` / Identity Assurance | `KycProfile` in `fin_identity` module |
| Verified Claims | Mapped to `KycStatus::Verified` |
| Trust Frameworks | Linked to `ComplianceFramework` |

---

## Keycloak Integration

SovereignStack ships with Keycloak OIDC support (see ROADMAP 2026.1). The integration extends to:

1. **Realm per organization** → `org://` twin
2. **Roles** → `capability://` tokens
3. **Groups** → Federation trust domains
4. **Token exchange** → Cross-node capability delegation (RFC-0026)

---

## Token Flow

```
User (operator://) → Keycloak OIDC → ID Token
    ↓
ss-identity validates token, creates capability://
    ↓
capability:// attached to session://
    ↓
Policy engine (ss-policy) enforces per-request
```

---

## Implementation Notes

1. **OIDC Discovery**: Nodes expose `/.well-known/openid-configuration` for federated identity.
2. **Token lifetime**: Aligned with session lifecycle (RFC-0009).
3. **Multi-provider**: Nodes can trust multiple OIDC providers for federated identity.
