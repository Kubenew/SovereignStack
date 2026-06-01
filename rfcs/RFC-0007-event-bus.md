# RFC-0007: Event Bus

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the Event Bus — an immutable, signed, publish/subscribe event system that serves as the backbone for all state changes, audit trails, and inter-component communication in SovereignStack.

## Motivation

Every state change in the system must be recorded, signed, and observable. The Event Bus provides event sourcing for full audit trails, enables reactive agents, and forms the foundation for federation replication.

## Specification

### Event Object

```json
{
  "id": "event://evt-a1b2c3d4",
  "type": "event",
  "owner": "node://origin-node",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:00:00Z",
  "signature": "sig:abc...",
  "provenance": [],
  "event": {
    "event_type": "agent.spawned",
    "version": 1,
    "source": "node://origin-node",
    "actor": "agent://creator",
    "timestamp": "2026-05-31T12:00:00.000Z",
    "payload": {
      "agent_uri": "agent://new-agent-001",
      "parent_session": "session://parent-001",
      "capabilities": ["capability://memory.store"]
    },
    "context": {
      "session_id": "session://parent-001",
      "trace_id": "trace-xyz-789",
      "jurisdiction": "EU"
    },
    "previous_event": "event://evt-00000001",
    "merkle_root": "sha256:abc123..."
  }
}
```

### Event Types Registry

| Event Type | Description | Category |
|------------|-------------|----------|
| `node.started` | Node came online | Lifecycle |
| `node.stopped` | Node went offline | Lifecycle |
| `agent.spawned` | Agent created | Lifecycle |
| `agent.terminated` | Agent destroyed | Lifecycle |
| `session.created` | Session opened | Lifecycle |
| `session.closed` | Session closed | Lifecycle |
| `capability.granted` | Capability issued | Security |
| `capability.revoked` | Capability revoked | Security |
| `capability.used` | Capability exercised | Audit |
| `policy.evaluated` | Policy decision made | Governance |
| `knowledge.created` | Knowledge stored | Data |
| `knowledge.updated` | Knowledge versioned | Data |
| `knowledge.queried` | Knowledge accessed | Data |
| `reason.recorded` | Reasoning trace saved | Intelligence |
| `federation.peer_discovered` | New peer found | Network |
| `federation.data_replicated` | Data synced | Network |

### Subscription Model

```json
{
  "subscription": {
    "id": "sub-001",
    "subscriber": "agent://monitor-agent",
    "event_types": ["agent.*", "capability.*"],
    "filter": {"jurisdiction": "EU"},
    "callback": "sip://callback-endpoint",
    "expires": "2026-06-01T12:00:00Z"
  }
}
```

Wildcard patterns follow MQTT-style:
- `agent.*` — all agent events
- `*.created` — all creation events
- `capability.granted` — exact match

### Delivery Guarantees

| Guarantee | Description |
|-----------|-------------|
| At-least-once | Default delivery |
| Ordered per-source | Events from same source in order |
| Exactly-once | With deduplication (idempotent consumers) |

### Event Store

Events are stored in an append-only, Merkle-chained structure:

```
Event 1 ──── hash ────► Event 2 ──── hash ────► Event 3
   │                       │                       │
   └── merkle_root ────────┴── merkle_root ────────┘
```

The Merkle root enables:
- Tamper detection
- Efficient sync between nodes
- Lightweight verification without full history

### Federation Replication

Events are the unit of federation replication. When two nodes are federated:

1. Node A publishes event
2. Event is signed and Merkle-rooted
3. Node B subscribes to Node A's event stream
4. Node B verifies signatures and Merkle proofs
5. Node B applies event locally (if policy allows)

## Security Considerations

- Every event is signed by its source
- Event stores are append-only (no deletion, only tombstones)
- Merkle chaining prevents retroactive tampering
- Subscriptions are capability-gated
- Event retention is governed by policy

## Reference Implementation

- `ss-kernel::eventbus` — kernel-level event bus
- `ss-eventbus` crate — distributed event store with Merkle chains
- Conformance tests: planned

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
