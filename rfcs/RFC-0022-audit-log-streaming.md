# RFC-0022: Audit Log Streaming

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0007, RFC-0012

## Summary

Defines the structured audit log format, streaming protocol, and immutable storage requirements for all SovereignStack operations.

## Specification

### Log Entry

```json
{
  "id": "audit://zcube-a/seq-1042",
  "timestamp": "2026-06-03T12:00:00.000Z",
  "actor": "agent://researcher-1",
  "action": "knowledge.create",
  "resource": "knowledge://physics/newton/v2",
  "result": "allowed",
  "capability": "capability://write-knowledge",
  "signature": "ed25519:base64url...",
  "merkle_proof": {"tree_root": "sha256:xyz...", "leaf_index": 1042, "siblings": ["sha256:..."]}
}
```

### Streaming

Entries are streamed via the event bus (RFC-0007) to subscribers. At-rest, they are stored in an append-only merkle tree for tamper evidence.

### Retention

- L1: 90 days
- L2: 365 days  
- L3: Indefinite (immutable WORM storage)

### Core Types

`AuditEntry`, `AuditStream`, `MerkleTree`, `RetentionPolicy`
