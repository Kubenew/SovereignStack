# RFC-0001: Sovereign Object Model

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the universal object model for all entities in the SovereignStack ecosystem. Every object — agent, session, memory, knowledge, artifact, workflow, policy, capability — inherits from this common base structure.

## Motivation

Interoperability requires a shared structural foundation. Every entity must be addressable, verifiable, and capable of provenance tracking. This RFC establishes the equivalent of Kubernetes' resource model for the intelligence network.

## Specification

### Universal Object Base

Every SovereignStack object **must** contain these fields:

```json
{
  "id": "agent://uuid-or-hash",
  "type": "agent|session|memory|knowledge|artifact|workflow|policy|capability",
  "owner": "node://owner-node",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:05:00Z",
  "signature": "ed25519:base64signature...",
  "provenance": [
    {
      "action": "created",
      "agent": "agent://creator",
      "timestamp": "2026-05-31T12:00:00Z"
    }
  ]
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | URI | Yes | Globally unique, resolvable URI (RFC-0002) |
| `type` | String | Yes | Object type identifier from registry |
| `owner` | URI | Yes | Node or agent that owns this object |
| `version` | SemVer | Yes | Semantic version of the object |
| `created` | ISO 8601 | Yes | Creation timestamp |
| `updated` | ISO 8601 | Yes | Last modification timestamp |
| `signature` | String | Yes | Cryptographic signature of the object |
| `provenance` | Array | Yes | Ordered list of provenance events |

### Type-Specific Extensions

Each object type extends the base with a typed payload:

```json
{
  "id": "agent://a1b2c3d4",
  "type": "agent",
  "owner": "node://bootstrap",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:00:00Z",
  "signature": "sig:abc...",
  "provenance": [],
  "agent_specific": {
    "public_key": "ed25519:deadbeef...",
    "capabilities": ["reason", "memory"]
  }
}
```

### Object Types Registry

| Type | URI Prefix | Payload Schema | Mutable |
|------|------------|----------------|---------|
| agent | `agent://` | AgentSchema | Yes (key rotation) |
| session | `session://` | SessionSchema | Yes (state changes) |
| memory | `memory://` | MemorySchema | No (immutable entries) |
| knowledge | `knowledge://` | KnowledgeSchema | No (versioned) |
| artifact | `artifact://` | ArtifactSchema | No (content-addressed) |
| workflow | `workflow://` | WorkflowSchema | Yes (definition updates) |
| policy | `policy://` | PolicySchema | Yes (versioned) |
| capability | `capability://` | CapabilitySchema | No (revocable) |

### Object Lifecycle

```
Created → Active → [Updated]* → Deprecated → Archived
                    → Revoked (capabilities)
                    → Tombstoned (deletions)
```

### Serialization

- Wire format: JSON (UTF-8)
- Canonical form: deterministic key ordering
- Binary format: CBOR (optional, for performance)

## Security Considerations

- All objects **must** be signed at creation
- Signature verification **must** precede any operation
- Objects are immutable after creation (new versions for changes)
- Provenance chain prevents undetected modification
- Owner field determines access control base

## Reference Implementation

- `ss-kernel::registry::ObjectEntry` — kernel-level registry
- `ss-cas` — content-addressed storage for immutable objects

## Backward Compatibility

Objects without the `provenance` field will be rejected as invalid after the deprecation period (2026-09-01).
