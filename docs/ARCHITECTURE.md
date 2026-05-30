# SovereignStack Architecture

## Overview

SovereignStack is a civilization-scale distributed intelligence infrastructure. This document describes the foundational architecture that all subsystems build upon.

## Core Abstraction: The Sovereign URI

The most important architectural decision in SovereignStack is that **everything is addressable**. Every entity, resource, and concept in the system has a globally unique, resolvable URI.

### URI Scheme

```
scheme://authority/path[?query][#fragment]
```

### Registered Schemes

| Scheme | Authority | Description | Example |
|---|---|---|---|
| `agent` | agent-name | Agent identity | `agent://researcher-1` |
| `org` | org-name | Organization | `org://acme` |
| `session` | session-id | Active session | `session://abc123` |
| `artifact` | artifact-hash | Produced artifact | `artifact://sha256:def456` |
| `memory` | memory-id | Memory object | `memory://xyz789` |
| `reason` | reasoning-id | Reasoning chain | `reason://decision-42` |
| `knowledge` | domain/path | Knowledge object | `knowledge://physics/newton` |
| `capability` | capability-name | Skill/capability | `capability://legal-review` |
| `workflow` | workflow-name | Workflow definition | `workflow://contract-analysis` |
| `contract` | contract-id | Agent contract | `contract://task-88` |
| `robot` | device-id | Physical device | `robot://drone-12` |
| `policy` | policy-name | Governance policy | `policy://gdpr-eu` |
| `node` | node-id | Network node | `node://homelab-1` |
| `event` | event-id | Event record | `event://evt-99` |

### URI Resolution

URIs resolve through the **Sovereign Name Service (SNS)**, which operates similarly to DNS but for intelligence objects:

1. **Local resolution** — Check local node registry
2. **Federation resolution** — Query federated peers via DHT
3. **Global resolution** — Broadcast capability query to network

## Layered Architecture

```
┌─────────────────────────────────────────────────┐
│                 Applications                     │
├─────────────────────────────────────────────────┤
│  ss-swarm  │  ss-workflow  │  ss-search         │
├─────────────────────────────────────────────────┤
│  ss-scheduler │ ss-routing │ ss-discovery       │
├─────────────────────────────────────────────────┤
│  ss-reason │ ss-kas │ ss-memory │ ss-twin       │
├─────────────────────────────────────────────────┤
│  ss-identity │ ss-capability │ ss-eventbus      │
├─────────────────────────────────────────────────┤
│  ss-cas │ ss-federation │ ss-policy             │
├─────────────────────────────────────────────────┤
│  ss-core │ ss-crypto                             │
└─────────────────────────────────────────────────┘
```

### Layer 0: Foundations (`ss-core`, `ss-crypto`)

- Sovereign URI parsing and resolution
- Ed25519 cryptographic primitives
- Content hashing (SHA-256)
- Common error types and result handling
- Timestamp and temporal types

### Layer 1: Infrastructure (`ss-cas`, `ss-federation`, `ss-policy`)

- Content-addressed immutable storage (Merkle trees)
- Peer discovery and sovereign routing
- Jurisdiction and governance policies

### Layer 2: Primitives (`ss-identity`, `ss-capability`, `ss-eventbus`)

- Universal Agent Identity with public keys
- Capability declaration, matching, and advertisement
- Event sourcing for all state changes

### Layer 3: Intelligence (`ss-reason`, `ss-kas`, `ss-memory`, `ss-twin`)

- Reasoning object storage and replay
- Knowledge addressing and versioning
- Tiered memory hierarchy (session → civilizational)
- Digital twin framework for physical systems

### Layer 4: Orchestration (`ss-scheduler`, `ss-routing`, `ss-discovery`)

- Compute scheduling across nodes
- Cognitive routing (route by capability, not address)
- Semantic DNS and capability search

### Layer 5: Collaboration (`ss-swarm`, `ss-workflow`, `ss-search`)

- Multi-agent swarm coordination
- Intelligence DAG execution
- Sovereign search across all addressable objects

## Event Sourcing

SovereignStack uses **event sourcing** as its primary state management pattern instead of CRUD databases. Every state change is an immutable event:

```rust
Event {
    id: EventId,
    timestamp: Timestamp,
    source: SovereignUri,
    event_type: EventType,
    payload: Bytes,
    signature: Signature,
}
```

Benefits:
- Complete audit trail
- Temporal queries (state at any point in time)
- Federation-friendly (events replicate naturally)
- Reproducibility (replay events to reconstruct state)

## Memory Hierarchy

```
Tier 0: Session Memory    (seconds–minutes)   — volatile, in-process
Tier 1: Personal Memory   (days–weeks)        — persisted, per-agent
Tier 2: Org Memory        (months–years)       — shared, organizational
Tier 3: Global Memory     (decades)            — civilizational knowledge
```

## Trust Model

Trust is not boolean. Every identity has:

```rust
TrustProfile {
    identity: SovereignUri,
    trust_score: f64,          // 0.0–1.0
    accuracy: f64,             // historical accuracy
    reliability: f64,          // uptime, completion rate
    latency_ms: u64,           // average response time
    verifications: Vec<Verification>,
    reputation_history: Vec<ReputationEvent>,
}
```

Trust is used for:
- **Routing decisions** — prefer higher-trust agents
- **Federation** — control which nodes can replicate
- **Capability matching** — weight trust in agent selection
- **Governance** — enforce minimum trust thresholds

## Federation Model

SovereignStack nodes form a **sovereign federation**:

- Each node is sovereign — controls its own data, policies, and trust
- Nodes discover peers via DHT (Kademlia-based)
- Data replication respects jurisdiction policies
- Events propagate through the event bus with trust filtering

## Protocol Convergence (SIP)

All domain-specific protocols converge into the **Sovereign Intelligence Protocol (SIP)**:

```
SEP (Session Exchange)     ─┐
SDP (Session Discovery)    ─┤
SAP (Session Artifact)     ─┼─→  SIP (Sovereign Intelligence Protocol)
SMP (Session Memory)       ─┤
AGP (Autonomous Governance)─┘
```

SIP is to intelligence networks what TCP/IP is to data networks.
