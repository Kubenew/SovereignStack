# SovereignStack Object Model

**Version:** 2.0
**Status:** Draft
**Related RFC:** RFC-0001, RFC-0060
**Related:** [SIRA](SIRA.md)

## Core Principles

All objects in SovereignStack follow a uniform structure defined by **Principle 4 (Address Everything)** and **Principle 5 (Verifiable Everything)**.

## Universal Object Structure

```json
{
  "uri": "agent://8f3c2a1d-...",
  "type": "agent",
  "quadrant": "operational",
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

## Four-Quadrant Classification

Every entity belongs to exactly one of four quadrants. This provides implementers a common mental model independent of any particular AI architecture (see [SIRA §3](SIRA.md)).

```
┌─────────────────────────────┬─────────────────────────────┐
│       COGNITIVE             │       OPERATIONAL           │
│                             │                             │
│  mind://                    │  workflow://                 │
│  reason://                  │  session://                  │
│  goal://                    │  agent://                    │
│  belief://                  │  artifact://                 │
│  knowledge://               │  checkpoint://               │
│                             │  scheduler://                │
├─────────────────────────────┼─────────────────────────────┤
│       GOVERNANCE            │       FEDERATION            │
│                             │                             │
│  policy://                  │  node://                     │
│  capability://              │  fabric://                   │
│  provenance://              │  routing://                  │
│  evidence://                │  gateway://                  │
│  constitution://            │  topology://                 │
│                             │  federation://               │
└─────────────────────────────┴─────────────────────────────┘
```

## Core Object Types

### Cognitive Objects

| Object | URI Scheme | Purpose |
|--------|-----------|---------|
| Mind | `mind://` | Root persistent cognitive state |
| Reason | `reason://` | Verifiable reasoning graph node |
| Goal | `goal://` | Active objective with completion criteria |
| Belief | `belief://` | Held proposition with confidence |
| Knowledge | `knowledge://` | Long-term, versioned facts |

### Operational Objects

| Object | URI Scheme | Purpose |
|--------|-----------|---------|
| Agent | `agent://` | Autonomous reasoning entity |
| Session | `session://` | Ephemeral interaction context |
| Workflow | `workflow://` | Executable process |
| Artifact | `artifact://` | Files, models, datasets |
| Checkpoint | `checkpoint://` | Serialized execution state |

### Governance Objects

| Object | URI Scheme | Purpose |
|--------|-----------|---------|
| Policy | `policy://` | Governance rules |
| Capability | `capability://` | Permission token |
| Provenance | `provenance://` | Causal creation chain |
| Evidence | `evidence://` | Verifiable audit evidence |

### Federation Objects

| Object | URI Scheme | Purpose |
|--------|-----------|---------|
| Node | `node://` | Physical or virtual host |
| Fabric | `fabric://` | Named AI compute fabric |
| Routing | `routing://` | Cognitive routing entry |
| Gateway | `gateway://` | Federation gateway |
| Topology | `topology://` | Named topology graph |

## Requirements

- Every object must be cryptographically signed
- Every object must support provenance tracking
- Every object must be addressable via URI
- Objects are immutable after creation (new versions created for changes)
- Every object must declare its quadrant
