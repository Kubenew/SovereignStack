# RFC-0006: Knowledge Objects

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the structure, lifecycle, and operations for Knowledge Objects — versioned, verifiable units of information that serve as the long-term memory of the network.

## Motivation

Unlike ephemeral Memory (session-scoped), Knowledge must persist, be versioned, support provenance, and be independently verifiable.

## Specification

### Knowledge Object Structure

```json
{
  "uri": "knowledge://sha256:a1b2c3d4...",
  "type": "knowledge",
  "version": "1.0.0",
  "created_at": "2026-05-31T12:00:00Z",
  "modified_at": "2026-05-31T12:00:00Z",
  "content_hash": "sha256:a1b2c3d4...",
  "previous_version": "knowledge://sha256:...",
  "signature": "...",
  "provenance": [
    {
      "action": "created",
      "agent": "agent://creator",
      "timestamp": "2026-05-31T12:00:00Z",
      "reason": "extraction://session-123"
    }
  ],
  "payload": {}
}
```

### Operations

- **Create** — New knowledge with provenance
- **Read** — Retrieve by URI or content hash
- **Update** — New version with pointer to previous
- **Delete** — Tombstone (never truly deleted)
- **Merge** — Combine two knowledge objects
- **Diff** — Compute semantic diff between versions

### Content Addressing

- Content is addressed by SHA-256 hash
- Immutable content never changes URI
- Updated content gets new URI (new hash)

### Query Interface

- Full-text search on payload
- Graph traversal on provenance
- Temporal queries (snapshots at time T)

## Security Considerations

- Knowledge objects are signed and immutable
- Access requires read capability
- Provenance chain prevents undetected modification

## Reference Implementation

- ss-kas crate: `crates/ss-kas/src/knowledge.rs`
