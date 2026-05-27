# SovereignStack Specifications

This directory contains formal specifications for SovereignStack subsystems and protocols.

## Current Specs

| Spec | Status | Description |
|---|---|---|
| [OASA](OASA.md) | Stable | Open Architecture Specification for Autonomous and Sovereign AI |
| [Runtime](rfcs/0001-runtime-spec.md) | Draft | Sovereign Runtime execution layer |

## Planned Specs

| Spec | Priority | Description |
|---|---|---|
| Node Specification | High | Node identity, minimum requirements, trust validation |
| Federation Protocol | High | Mesh networking, trust propagation, offline sync |
| Memory Specification | Medium | Vector memory, state synchronization, CRDT replication |
| Agent API | Medium | Agent lifecycle, scheduling, memory attachment |
| Identity Specification | Medium | SPIFFE/SPIRE integration, hardware attestation |

## Spec Lifecycle

Each spec follows the [RFC process](../rfcs/0000-rfc-process.md):

```
Draft → Discussion → Accepted → Implemented → Stable → Deprecated
```
