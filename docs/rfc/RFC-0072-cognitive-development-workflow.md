# RFC-0072: Cognitive Development Workflow

**Status:** Draft
**URI Schemes:** `idea://`, `research://`, `decision://`, `architecture://`, `spec://`, `build://`, `release://`, `project://`, `flow://`
**Depends on:** RFC-0001 (Sovereign Object Model), RFC-0013 (Provenance Graph)
**Related:** RFC-0045 (Meta-Cognition), RFC-0051 (Explainability & Provenance)

## Abstract

This RFC defines a **Cognitive Software Development Lifecycle (Cognitive SDLC)** — a standard protocol for managing the evolution of knowledge, decisions, and implementation as first-class addressable objects. It introduces nine URI schemes representing distinct cognitive stages of development, enabling full traceability, provenance, and governance of the engineering process itself.

## Motivation

Traditional SDLC tools (issue trackers, wikis, docs) store artifacts as opaque blobs with no machine-readable semantics. As AI agents increasingly participate in development, the process itself must become an addressable, auditable cognitive pipeline. This RFC treats development not as file changes but as a flow of cognitive states — ideas maturing into research, architecture decisions, specifications, build plans, and releases — each with its own provenance chain.

## The Cognitive Pipeline

```
                    ┌─────────────┐
                    │  Research   │  research://
                    │  Analyst    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │    Idea     │  idea://
                    │   Keeper    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │    Flow     │  flow://
                    │   Router    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Art.       │  architecture://
                    │  Guard      │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Decision   │  decision://
                    │  Manager    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │   Spec      │  spec://
                    │  Guardian   │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │   Build     │  build://
                    │  Planner    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Release    │  release://
                    │  Governor   │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  Project    │  project://
                    │  Controller │
                    └─────────────┘
```

## URI Schemes

### `idea://` — Raw Idea / Hypothesis

Stores unfiltered ideas, hypotheses, and observations. Ideas are NOT architecture decisions or specs — they are raw cognitive material.

```
idea://<project>/<id>
```

Example: `idea://project-cortex/042`

```json
{
  "id": "idea://project-cortex/042",
  "status": "draft",
  "title": "Cognitive SDLC with addressable objects",
  "source": "architecture-review",
  "author": "agent://architect-1",
  "confidence": 0.7,
  "tags": ["sdlc", "uri", "governance"],
  "created_at": "2026-07-18T10:00:00Z",
  "related_research": ["research://MCTS/arXiv-2501.12345"]
}
```

### `research://` — Research Artifact

Links to external or internal research: papers, RFCs, experiments, benchmarks.

```
research://<topic>/<source>
```

Example: `research://MCTS/arXiv-2501.12345`

### `decision://` — Architectural Decision Record

A formal, timestamped decision with rationale, alternatives considered, and outcome.

```
decision://<project>/<id>
```

Example: `decision://project-cortex/ADR-007`

```json
{
  "id": "decision://project-cortex/ADR-007",
  "status": "accepted",
  "title": "Use graph-based search instead of tree",
  "context": "RFC-0070 review identified need for cyclic graph support",
  "alternatives": ["strict-tree", "dag-only", "full-graph"],
  "decision": "full-graph",
  "rationale": "Future-proof for graph-of-thought and cyclic reasoning",
  "consequences": "More complex serialization, richer provenance",
  "date": "2026-07-18",
  "author": "agent://architect-1",
  "signature": "ed25519:..."
}
```

### `architecture://` — Architecture Boundary

Defines a module boundary, ownership, and interface contract.

```
architecture://<module>/<name>
```

Example: `architecture://ss-policy/module-boundary`

### `spec://` — Feature Specification

A formal specification ready for implementation. Created only after a decision has been accepted.

```
spec://<feature>/<name>
```

Example: `spec://cognitive-router/routing-logic`

### `build://` — Build Plan

An execution plan decomposed from a spec into epics, tasks, milestones.

```
build://<project>/<epic>
```

Example: `build://project-cortex/epic-3`

### `release://` — Release Artifact

A verified, signed release with changelog, license checks, and conformance status.

```
release://<project>/<version>
```

Example: `release://sovereignstack/v2026.3`

### `project://` — Project State

The global state of a project — active milestones, current phase, checkpoints.

```
project://<id>
```

Example: `project://cortex`

### `flow://` — Workflow Routing

A workflow rule or routing path connecting cognitive stages.

```
flow://<router>/<route>
```

Example: `flow://router/idea-to-spec`

## Role Definitions

| Role | Responsibility | Primary URI | Secondary URIs |
|------|---------------|-------------|----------------|
| **Research Analyst** | Gathers and analyzes external knowledge | `research://` | `knowledge://` |
| **Idea Keeper** | Stores raw ideas, prevents premature hardening | `idea://` | — |
| **Flow Router** | Routes ideas to the correct next stage | `flow://` | `workflow://` |
| **Architecture Guard** | Validates architectural integrity | `architecture://` | — |
| **Decision Manager** | Records and enforces decisions | `decision://` | `governance://` |
| **Spec Guardian** | Gatekeeps official specifications | `spec://` | `artifact://` |
| **Build Planner** | Decomposes specs into executable plans | `build://` | — |
| **Release Governor** | Validates release readiness | `release://` | — |
| **Project Controller** | Maintains global context and lifecycle | `project://` | — |

## Security Considerations

- **Decision Integrity:** All `decision://` objects MUST be signed by the author and immutable once accepted. Amendments create new decision objects referencing the superseded one.
- **Idea-to-Spec Boundary:** No `idea://` object may be promoted to `build://` without passing through `decision://` and `spec://`. The Flow Router MUST enforce this.
- **Provenance:** All state transitions (idea → decision → spec → build → release) MUST be recorded in the provenance graph (`ss-provenance`).
- **Release Signing:** Every `release://` object MUST be signed by the Release Governor identity and include a reference to the conformance test results.

## Conformance

To claim conformance with this RFC, an implementation MUST:

1. Support all nine URI schemes with the described semantics.
2. Enforce the pipeline ordering: `research → idea → flow → architecture → decision → spec → build → release`.
3. Record all stage transitions in the provenance graph.
4. Sign all `decision://` and `release://` objects.

## References

- RFC-0001: Sovereign Object Model
- RFC-0013: Provenance Graph
- RFC-0045: Meta-Cognition
- RFC-0051: Explainability & Provenance
- RFC-0070: Search Objects
- RFC-0071: Search Execution Protocol
