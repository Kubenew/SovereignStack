# SovereignStack Object Model

**Version:** 1.0
**Status:** Draft
**Related RFC:** RFC-0001

## Core Principles

All objects in SovereignStack follow a uniform structure defined by **Principle 4 (Address Everything)** and **Principle 5 (Verifiable Everything)**.

## Universal Object Structure

```json
{
  "uri": "agent://8f3c2a1d-...",
  "type": "agent",
  "version": "1.2.3",
  "created_at": "2026-05-31T12:00:00Z",
  "modified_at": "2026-05-31T12:05:00Z",
  "identity": {
    "public_key": "...",
    "signature": "...",
    "provenance": {}
  },
  "metadata": {
    "owner": "node://...",
    "jurisdiction": "EU",
    "tags": ["finance", "high-assurance"]
  },
  "payload": {},
  "capabilities": ["capability://read-memory"],
  "audit": {
    "merkle_root": "...",
    "previous_hash": "..."
  }
}
```

## Core Object Types

| Object | URI Scheme | Purpose |
|---|---|---|
| Agent | `agent://` | Autonomous reasoning entity |
| Session | `session://` | Ephemeral interaction context |
| Memory | `memory://` | Short-term state |
| Knowledge | `knowledge://` | Long-term, versioned facts |
| Artifact | `artifact://` | Files, models, datasets |
| Workflow | `workflow://` | Executable process |
| Capability | `capability://` | Permission token |
| Policy | `policy://` | Governance rules |
| Node | `node://` | Physical or virtual host |

## Requirements

- Every object must be cryptographically signed
- Every object must support provenance tracking
- Every object must be addressable via URI
- Objects are immutable after creation (new versions created for changes)
