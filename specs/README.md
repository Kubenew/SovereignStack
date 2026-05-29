# SovereignStack Specifications

This directory contains formal specifications for SovereignStack subsystems and protocols.

## Current Specs

| Spec | Status | Description |
|---|---|---|---|
| [OASA](OASA.md) | Stable | Open Architecture Specification for Autonomous and Sovereign AI |
| [Runtime](/rfcs/0001-runtime-spec.md) | Draft | Sovereign Runtime execution layer |
| [Node Identity](/rfcs/0003-node-identity.md) | Draft | Node identity, certificate model, TPM attestation |
| [Federation Protocol](/rfcs/0004-federation-protocol.md) | Draft | Mesh networking, CRDT sync, jurisdictional gating |
| [Agent API](/rfcs/0005-agent-api.md) | Draft | Agent lifecycle, scheduling, memory attachment, tool execution |
| [Memory](/rfcs/0006-memory-spec.md) | Draft | Vector store, KV cache, event log, CRDT sync, encryption |
| [GraphQL API](/docs/api/graphql.md) | Implemented | Dual REST + GraphQL gateway with introspection |
| [Enterprise Platform](/docs/enterprise/index.md) | Implemented | Support contracts, SLA, managed updates, deployment audits |
| [Certification Program](/docs/certification/index.md) | Implemented | Certified Node, Runtime, Federation with registry API |
| [Secure Weight Federation](/docs/federation/weight-federation.md) | Implemented | Sharded cross-node inference without weight sharing |

## Planned Specs

| Spec | Priority | Description |
|---|---|---|
| Identity Specification | Medium | SPIFFE/SPIRE integration, hardware attestation |
| Security Audit | Low | Formal security audit and certification |
| Multi-Model Orchestration | Low | Model routing, fallback, ensemble inference |

## Spec Lifecycle

Each spec follows the [RFC process](../rfcs/0000-rfc-process.md):

```
Draft → Discussion → Accepted → Implemented → Stable → Deprecated
```
