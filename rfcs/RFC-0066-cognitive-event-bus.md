# RFC-0066: Cognitive Event Bus (CEB)

**Status:** Draft | **Type:** Standard | **Created:** 2026-07-16 | **Depends On:** RFC-0007, RFC-0060  
**Protocol ID:** CEB

## Abstract

Defines the Cognitive Bus — an event-driven coordination protocol replacing synchronous chat conversations with asynchronous, typed events. CEB enables massively parallel multi-agent swarms by decoupling execution, reasoning, and memory updates.

## Motivation

Current agentic architectures rely on blocking, synchronous conversations (Agent A talks to Agent B, waits for reply). This limits concurrency, creates deadlocks, and scales poorly. The Cognitive Event Bus shifts the paradigm to event-driven choreography.

## Specification

### 1. The Event-Driven Paradigm

Instead of a linear chat, progress happens via events:

1. `goal.created` → Supervisor Mind creates a goal.
2. Planner Agent reacts → publishes `reason.completed` (the plan).
3. Reasoner Agent reacts → publishes `reason.started`.
4. Auditor Agent reacts → validates against policy, publishes `policy.validated`.
5. Scheduler reacts → dispatches execution, publishes `scheduler.dispatched`.

### 2. Event Envelope Schema

Every event MUST follow this normative envelope:

```json
{
  "event_id": "event://evt-042",
  "event_type": "reason.completed",
  "timestamp": "2026-07-16T12:00:00Z",
  "source": "agent://reasoner-1",
  "session": "session://finance",
  "payload_uri": "reason://sha256:abc123",
  "provenance": {
    "causal_parent": "event://evt-041",
    "signature": "ed25519:base64url..."
  }
}
```

*Note: The payload itself is usually referenced by URI (`payload_uri`) rather than embedded, following the pointer-passing principles of DMP (RFC-0063).*

### 3. Event Taxonomy

CEB defines a standard taxonomy of cognitive events. Implementations MUST support these base types.

#### Goal Events
- `goal.created`: A new objective is established.
- `goal.updated`: Objective parameters modified.
- `goal.completed`: Objective successfully met.
- `goal.failed`: Objective failed or deemed impossible.

#### Reason Events
- `reason.started`: An agent begins a reasoning block (e.g., MCTS search).
- `reason.completed`: A reasoning block concluded successfully.
- `reason.cached`: A reasoning result was added to the semantic cache.
- `reason.invalidated`: Previous reasoning is no longer valid.

#### Memory Events
- `memory.updated`: Context or knowledge base modified.
- `memory.evicted`: Context dropped (e.g., TTL expired).
- `memory.synced`: Delta sync completed across nodes.

#### Policy Events
- `policy.validated`: An action or plan passed governance checks.
- `policy.denied`: An action or plan violated governance checks.
- `policy.updated`: A governance rule changed.

#### Capability Events
- `capability.granted`: A permission token was issued.
- `capability.revoked`: A permission token was revoked.
- `capability.expired`: A permission token time-out.

#### Operational Events
- `checkpoint.created`: State successfully serialized.
- `scheduler.dispatched`: Workload assigned to a node.
- `agent.started`: Agent lifecycle began.
- `agent.terminated`: Agent lifecycle ended.

### 4. Event Subscriptions and Routing

Agents subscribe to event types and session scopes.

```json
{
  "action": "subscribe",
  "agent": "agent://auditor-1",
  "filters": {
    "event_type": ["reason.completed"],
    "session": "session://finance"
  }
}
```

The underlying message transport (e.g., Libp2p Gossipsub, NATS) handles the efficient delivery of these events to subscribers.

## Core Types

```rust
pub struct CognitiveEvent {
    pub event_id: SovereignUri,
    pub event_type: EventType,
    pub timestamp: Timestamp,
    pub source: SovereignUri,
    pub session: SovereignUri,
    pub payload_uri: Option<SovereignUri>,
    pub provenance: EventProvenance,
}

pub enum EventType {
    GoalCreated,
    GoalCompleted,
    ReasonStarted,
    ReasonCompleted,
    MemoryUpdated,
    PolicyValidated,
    PolicyDenied,
    // ... maps to taxonomy
    Custom(String),
}

pub struct EventProvenance {
    pub causal_parent: Option<SovereignUri>,
    pub signature: String,
}
```

## Security Considerations

- **Event Forgery**: All events MUST be cryptographically signed by the `source` agent. Subscribers MUST verify this signature.
- **Causal Consistency**: The `causal_parent` field ensures a verifiable DAG (Directed Acyclic Graph) of events, preventing replay attacks or out-of-order execution logic flaws.

## Conformance Impact

- Required for **SIRA-2** conformance.
- Replaces/Extends RFC-0007 (Event Bus).
