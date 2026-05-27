# SovereignStack Specifications

This directory contains formal specifications for SovereignStack subsystems and protocols.

## Current Specs

| Spec | Status | Description |
|---|---|---|
| [OASA](OASA.md) | Stable | Open Architecture Specification for Autonomous and Sovereign AI |
| [Runtime](/rfcs/0001-runtime-spec.md) | Draft | Sovereign Runtime execution layer |
| [Node Identity](/rfcs/0003-node-identity.md) | Draft | Node identity, certificate model, TPM attestation |
| [Federation Protocol](/rfcs/0004-federation-protocol.md) | Draft | Mesh networking, CRDT sync, jurisdictional gating |
| [Agent API](/rfcs/0005-agent-api.md) | Draft | Agent lifecycle, scheduling, memory attachment, tool execution |

## Planned Specs

| Spec | Priority | Description |
|---|---|---|
| Memory Specification | Medium | Vector memory, state synchronization, CRDT replication |
| Identity Specification | Medium | SPIFFE/SPIRE integration, hardware attestation |
| Security Audit | Low | Formal security audit and certification |

## Spec Lifecycle

Each spec follows the [RFC process](../rfcs/0000-rfc-process.md):

```
Draft → Discussion → Accepted → Implemented → Stable → Deprecated
```
