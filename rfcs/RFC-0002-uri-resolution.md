# RFC-0002: URI Resolution Mechanism

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines how SovereignStack URIs are resolved to their referenced objects, supporting local-first resolution with federated fallback.

## Motivation

Objects must be locatable across the distributed network while respecting sovereignty boundaries.

## Specification

### Resolution Order

1. **Local Cache** — Check local content-addressed store
2. **Local Node** — Query local node's object registry
3. **Trusted Peers** — Query configured trusted peers
4. **Federation** — Query federation discovery (if policy allows)

### URI Normalization

- All URIs are normalized to lowercase before resolution
- Query parameters are preserved in canonical order
- Fragments are resolved server-side

### Response Format

```json
{
  "uri": "agent://abc123",
  "object": { ... },
  "resolved_by": "node://resolver-node",
  "provenance": [...]
}
```

### Error Responses

- `404` — Not found
- `403` — Forbidden (no capability)
- `410` — Object deleted (tombstone)
- `504` — Federation timeout

## Security Considerations

- Resolution requires appropriate capability
- Resolution chains must be verifiable
- Federation resolution is opt-in per policy

## Reference Implementation

- ss-core crate: `crates/ss-core/src/resolver.rs`
