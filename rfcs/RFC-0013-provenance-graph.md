# RFC-0013: Provenance Graph

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0012

## Summary

Defines the provenance graph data model for tracking the lineage of every SovereignStack object — how it was created, transformed, and by whom.

## Specification

### Provenance Record

```json
{
  "id": "prov://abc123",
  "entity": "knowledge://physics/newton/v2",
  "wasGeneratedBy": {"activity": "reasoning://decision-42", "time": "2026-06-03T12:00:00Z"},
  "used": [{"entity": "knowledge://physics/newton/v1", "role": "source"}],
  "wasAttributedTo": "agent://researcher-1",
  "signature": {"algorithm": "ed25519", "value": "base64url..."}
}
```

### Graph Operations

- `expand(entity)` — walk forward/backward through provenance links
- `verify(entity)` — check cryptographic integrity of entire chain
- `diff(v1, v2)` — compute changeset between two versions

## Core Types

`ProvenanceRecord`, `ProvenanceGraph`, `ProvEdge`
