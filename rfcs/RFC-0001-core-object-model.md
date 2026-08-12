# RFC-0001: Sovereign Object Model & Universal Addressing

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-30
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the universal object model for all entities in the SovereignStack ecosystem — plus the Sovereign URI, the addressing scheme that makes every object globally resolvable. Every object — agent, session, memory, knowledge, artifact, workflow, policy, capability — inherits from a common base structure and is addressable via a registered URI scheme.

## Motivation

Interoperability requires a shared structural foundation and a uniform addressing mechanism. Every entity must be addressable, verifiable, and capable of provenance tracking. This RFC establishes the equivalent of Kubernetes' resource model for the intelligence network, extended with federation-grade addressing.

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

### Universal Addressing

A Sovereign URI conforms to the standard URI syntax defined in RFC 3986:

```
scheme://authority/path[?query][#fragment]
```

### Registered Schemes

| Scheme | Authority | Description |
|---|---|---|
| `agent` | Agent Name | Persistent identity of an AI agent |
| `org` | Org Name | Organizational boundary |
| `session` | Session ID | An active, multiplexed execution session |
| `artifact` | SHA-256 Hash | Immutable output produced by an agent |
| `memory` | Memory ID | A stateful memory object (Tier 0-3) |
| `reason` | Reason ID | An auditable reasoning chain |
| `knowledge` | Domain/Topic | Curated knowledge objects |
| `capability` | Skill Name | Advertised agent capability |
| `workflow` | DAG Name | Intelligence DAG definition |
| `contract` | Contract ID | Verifiable commitment between agents |
| `robot` | Device ID | Digital twin of a physical system |
| `policy` | Policy Name | Machine-readable governance rule |
| `node` | Node ID | A physical or virtual SovereignStack peer |
| `event` | Event ID | An immutable state change record |

### Resolution Mechanism

Sovereign URIs are resolved via the Sovereign Name Service (SNS), which operates in three tiers:
1. **Local:** Checked against the node's local memory store or Identity Registry.
2. **Federated:** Resolved via the libp2p Kademlia Distributed Hash Table (DHT).
3. **Global:** Resolved via broadcast capability query (Semantic DNS).

Formal URI grammar and resolution procedures are defined in RFC-0002.

### Address Examples

- `agent://legal-reviewer-alpha`
- `artifact://sha256:d8a5...9f2c`
- `capability://contract-analysis?language=cs`
- `knowledge://physics/newton-laws/v2.1`

## Type-Specific Extensions

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
- URIs themselves carry no trust; to verify an object referenced by a URI, retrieve it and verify its signature against the creator's public key (RFC-0030)

## Reference Implementation

- `ss-kernel::registry::ObjectEntry` — kernel-level registry
- `ss-cas` — content-addressed storage for immutable objects

## Backward Compatibility

Objects without the `provenance` field will be rejected as invalid after the deprecation period (2026-09-01).
