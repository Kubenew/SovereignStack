# SPIFFE/SPIRE Protocol Mapping

**Version:** 1.0  
**Status:** Draft  
**Related:** [ss-identity](../../ss-identity/) · [ss-kernel](../../ss-kernel/) · [ss-federation](../../ss-federation/)

---

## Overview

[SPIFFE](https://spiffe.io/) (Secure Production Identity Framework for Everyone) provides a standard for identifying and securing communications between workloads. [SPIRE](https://spiffe.io/docs/latest/spire-about/) is the production-ready implementation.

SovereignStack uses SPIFFE/SPIRE for workload-level identity, complementing the higher-level `agent://` and `person://` identities with infrastructure-level authentication.

---

## Identity Hierarchy

```
                SovereignStack Identity Layers
┌──────────────────────────────────────────────────────┐
│  Layer 3: Entity Twins                                │
│  person://, company://, bank://                       │
│  → Long-lived, human-meaningful identities            │
├──────────────────────────────────────────────────────┤
│  Layer 2: Agent Identity (UAI)                        │
│  agent://<uuid-or-did>                                │
│  → Ed25519 keypairs, DID anchoring                    │
├──────────────────────────────────────────────────────┤
│  Layer 1: Workload Identity (SPIFFE)                  │
│  spiffe://<trust-domain>/<workload-path>              │
│  → X.509 SVIDs, auto-rotated, infrastructure-level   │
└──────────────────────────────────────────────────────┘
```

---

## SPIFFE ID Mapping

| SPIFFE ID | SovereignStack Equivalent |
|---|---|
| `spiffe://cluster.local/ns/default/sa/ss-node` | `node://` identity |
| `spiffe://cluster.local/ns/agents/sa/agent-42` | `agent://` workload process |
| `spiffe://cluster.local/ns/economy/sa/payment-gw` | `ss-economy` service identity |
| `spiffe://cluster.local/ns/federation/sa/relay` | `gateway://` federation relay |

---

## SVID Usage

| SovereignStack Component | SVID Usage |
|---|---|
| `ss-kernel` | Validates SVID on all inter-service calls |
| `ss-federation` | Presents SVID during federation handshake |
| `ss-economy` | Authenticates payment gateway calls |
| `reference-node` | Fetches SVID on startup for node identity |
| `ss-eventbus` | mTLS with SVID for event stream authentication |

---

## Trust Domain Federation

SPIFFE trust domain federation maps to SovereignStack federation:

| SPIFFE Concept | SovereignStack Concept |
|---|---|
| Trust Domain | `org://` + `node://` cluster |
| Trust Bundle | Federation trust anchor exchange |
| Federation API | `gateway://` federation protocol (RFC-0035) |

---

## Deployment

```yaml
# SPIRE Agent config excerpt for SovereignStack
spire-agent:
  trust_domain: "sovereignstack.local"
  server_address: "spire-server:8081"
  workload_api_socket: "/run/spire/sockets/agent.sock"
  
  registration_entries:
    - spiffe_id: "spiffe://sovereignstack.local/ss-node"
      selectors:
        - type: k8s
          value: "ns:sovereign-stack"
```

---

## Implementation Notes

1. **Auto-rotation**: SVIDs rotate automatically; `ss-identity` caches and refreshes them.
2. **Audit attribution**: SPIFFE IDs are logged in the Merkle audit trail for workload-level attribution.
3. **Confidential computing**: SVIDs can be attested via SGX/SEV-SNP enclaves (see 2027.1 roadmap).
