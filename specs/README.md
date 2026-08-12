# SovereignStack Specifications

This directory contains formal specifications for SovereignStack subsystems and protocols.

## Current Specs

| Spec | Status | Description |
|---|---|---|---|
| [OASA](OASA.md) | Stable | Open Architecture Specification for Autonomous and Sovereign AI |
| [Session Runtime](/rfcs/RFC-0003-session-runtime.md) | Draft | Sovereign Runtime execution layer |
| [Identity & DID Resolution](/rfcs/RFC-0011-identity-did-resolution.md) | Draft | Node/agent identity, certificate model, TPM attestation |
| [Federation Routing](/rfcs/RFC-0008-federation-routing.md) | Draft | Mesh networking, discovery, trust negotiation |
| [Agent Communication](/rfcs/RFC-0014-agent-communication.md) | Draft | Agent lifecycle, scheduling, memory attachment, tool execution |
| [Sovereign Memory Protocol](/rfcs/RFC-0017-sovereign-memory-protocol.md) | Draft | Vector store, KV cache, event log, CRDT sync, encryption |
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
