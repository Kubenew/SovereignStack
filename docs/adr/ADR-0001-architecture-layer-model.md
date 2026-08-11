# ADR-0001: Architecture Layer Model

## Status: ACCEPTED — No migration before v0.6 retrospective

## Context
The current six-layer architecture (Applications -> Economic -> Intelligence ->
Governance -> Fabric -> Kernel) is conceptually elegant but creates classification
ambiguity for cross-cutting operations.

## Current Model (Six Layers)
Applications -> Economic -> Intelligence -> Governance -> Fabric -> Kernel

## Alternative Under Consideration (Four Layers)
Profiles -> Governance -> Execution -> Fabric

## Decision
Freeze the six-layer model for v0.5. Test its boundaries through implementation.
Reconsider at v0.6 retrospective based on concrete implementation friction.

## Criteria for Reconsideration
- >=3 cross-layer dependency cycles discovered during v0.5 implementation
- External contributor confusion documented in >=5 issues
- Conformance harness requires layer-specific logic that doesn't fit cleanly
