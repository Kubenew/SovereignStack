# Sovereign Intelligence Reference Architecture (SIRA)

**Version:** 1.0  
**Status:** Living Document  
**Maintained by:** OASA Technical Steering Committee  
**Last Updated:** July 2026  
**See also:** [SCALING-AGI.md](SCALING-AGI.md) (production deployment), [RFC-0060](rfcs/RFC-0060-cognitive-mesh-architecture.md) (mesh implementation)

---

## Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-07 | 1.0 | Initial release — four-quadrant object model, protocol stack, Cognitive Bus, 3-tier deployment |

## 1. Purpose

SIRA defines the normative reference architecture for SovereignStack — a distributed operating system for intelligence. It establishes:

- A **four-quadrant object model** organizing every addressable entity
- A **layered protocol stack** for cognitive interoperability
- A **three-tier deployment topology** for scalable federation
- A **Cognitive Bus** event model replacing synchronous chat orchestration

SIRA is implementation-independent. It specifies *behavior* and *interfaces*, not transport protocols or serialization formats. Whether future systems are based on transformers, neurosymbolic architectures, or something entirely different, they can exchange standardized objects through open protocols.

---

## 2. Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Sovereign First** | Intelligence runs under the owner's control. No implicit external dependencies. |
| 2 | **Offline First** | Every node operates autonomously. Federation is additive, never required. |
| 3 | **Verify Everything** | All objects are signed, all actions produce provenance. |
| 4 | **Address Everything** | Every entity has a globally unique, resolvable URI. |
| 5 | **Event-Driven Coordination** | Agents communicate through events, not synchronous conversations. |
| 6 | **Transport-Agnostic** | Standards specify behavior. Implementations choose transport (libp2p, QUIC, NATS, gRPC, MQTT, WebTransport). |
| 7 | **Serialization-Agnostic** | Normative object schemas. Any wire format (Protobuf, CBOR, FlatBuffers, Cap'n Proto, JSON). |
| 8 | **Capability-Based Security** | Access governed by delegable capability tokens, not ambient authority. |

---

## 3. Four-Quadrant Object Model

Every entity in SovereignStack belongs to exactly one of four quadrants. This classification provides implementers a common mental model independent of any particular AI architecture.

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

### 3.1 Cognitive Objects

Represent persistent cognitive state — the "thinking" substrate.

| URI Scheme | Purpose | Lifecycle |
|------------|---------|-----------|
| `mind://` | Root persistent cognitive state (goals, beliefs, knowledge, world model) | Long-lived, versioned |
| `reason://` | Verifiable reasoning graph node (content-addressed) | Immutable after creation |
| `goal://` | Active objective with completion criteria | Created → Active → Completed/Failed |
| `belief://` | Held proposition with confidence and evidence | Versioned, revisable |
| `knowledge://` | Long-term, versioned factual knowledge | Append-only, versioned |

### 3.2 Operational Objects

Represent active computation and execution state.

| URI Scheme | Purpose | Lifecycle |
|------------|---------|-----------|
| `agent://` | Autonomous reasoning entity with persistent identity | Persistent |
| `session://` | Bounded cognitive process (isolated namespace) | Ephemeral |
| `workflow://` | Executable process definition | Versioned |
| `artifact://` | Produced files, models, datasets | Immutable, content-addressed |
| `checkpoint://` | Serialized execution state for recovery | Immutable snapshots |

### 3.3 Governance Objects

Represent policy, authorization, and auditability.

| URI Scheme | Purpose | Lifecycle |
|------------|---------|-----------|
| `policy://` | Governance rules and constraints | Versioned |
| `capability://` | Delegable permission token | Time/scope-bounded |
| `provenance://` | Causal chain of object creation | Append-only |
| `evidence://` | Verifiable audit evidence | Immutable, signed |

### 3.4 Federation Objects

Represent infrastructure, networking, and cross-node coordination.

| URI Scheme | Purpose | Lifecycle |
|------------|---------|-----------|
| `node://` | Physical or virtual host | Persistent |
| `fabric://` | Named AI compute fabric | Persistent |
| `routing://` | Cognitive routing entry | Dynamic |
| `gateway://` | Federation gateway | Persistent |
| `topology://` | Named topology graph | Versioned |

---

## 4. Protocol Stack

SIRA defines a layered protocol stack analogous to TCP/IP, but designed for cognitive interoperability rather than data networking.

```
┌──────────────────────────────────────────────┐
│              APPLICATION LAYER               │
│  User applications, SDKs, agent frameworks   │
├──────────────────────────────────────────────┤
│              COGNITIVE LAYER                 │
│  CRP (Cognitive Router) · CEB (Event Bus)   │
│  DMP (Distributed Memory) · MAC (Consensus) │
├──────────────────────────────────────────────┤
│              AGENT LAYER                     │
│  SAP (Agent Protocol) · SXP (Session Exch.) │
│  CDP (Capability Delegation)                │
├──────────────────────────────────────────────┤
│              GOVERNANCE LAYER                │
│  Policy Engine · Provenance · Evidence       │
│  Jurisdiction Compliance · Audit             │
├──────────────────────────────────────────────┤
│              FEDERATION LAYER                │
│  SIP (Intelligence Protocol) · Federation    │
│  AFS (Fabric Scheduling) · SMR (Routing)     │
├──────────────────────────────────────────────┤
│              INFRASTRUCTURE LAYER            │
│  Kubernetes · Containers · GPUs · Network    │
│  Storage · TPM · HSM · Confidential Compute  │
└──────────────────────────────────────────────┘
```

### 4.1 Protocol Family

| Protocol | Full Name | Layer | Purpose | RFC |
|----------|-----------|-------|---------|-----|
| **SIP** | Sovereign Intelligence Protocol | Federation | Base transport and node discovery | RFC-0004 |
| **SAP** | Sovereign Agent Protocol | Agent | Agent lifecycle management | RFC-0005 |
| **SMP** | Sovereign Memory Protocol | Agent | Memory synchronization | — |
| **CRP** | Cognitive Router Protocol | Cognitive | Semantic routing of cognitive requests | RFC-0061 |
| **SXP** | Session Exchange Protocol | Agent | Cross-session state sharing | RFC-0062 |
| **DMP** | Distributed Memory Protocol | Cognitive | Pointer-based memory exchange | RFC-0063 |
| **AFS** | AI Fabric Scheduling Protocol | Federation | Multi-dimensional compute scheduling | RFC-0064 |
| **CDP** | Capability Delegation Protocol | Agent | Scoped capability transfer | RFC-0065 |
| **CEB** | Cognitive Event Bus Protocol | Cognitive | Event-driven agent coordination | RFC-0066 |
| **CKP** | Checkpoint & Recovery Protocol | Agent | Session state persistence and restore | RFC-0067 |
| **MAC** | Multi-Agent Consensus Protocol | Cognitive | Distributed decision agreement | RFC-0068 |
| **SMR** | Semantic Routing Protocol | Federation | Content-based message routing | RFC-0069 |

---

## 5. Cognitive Mesh Architecture

### 5.1 Concept

The Cognitive Mesh replaces monolithic agent orchestrators with a decentralized, event-driven architecture. Each agent is an independent sovereign object with its own lifecycle, identity, capabilities, and policies.

```
                           User
                            │
                            ▼
                    ┌───────────────┐
                    │  Supervisor   │
                    │    Mind       │
                    └───────┬───────┘
                            │
     ┌──────────┬───────────┼───────────┬──────────┐
     │          │           │           │          │
     ▼          ▼           ▼           ▼          ▼
 ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
 │Planner │ │Reasoner│ │ Coder  │ │ Memory │ │Auditor │
 │agent://│ │agent://│ │agent://│ │agent://│ │agent://│
 └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### 5.2 Session Isolation

Sessions function as **cognitive namespaces** — isolated execution environments analogous to Kubernetes namespaces:

```
session://finance     session://robotics    session://legal
    │                     │                     │
    ├── memories          ├── memories          ├── memories
    ├── reasoning         ├── reasoning         ├── reasoning
    ├── tools             ├── tools             ├── tools
    ├── capabilities      ├── capabilities      ├── capabilities
    └── policies          └── policies          └── policies
```

Nothing leaks between sessions automatically. Cross-session exchange requires explicit capability grants.

### 5.3 Cognitive Router

Instead of agents calling each other directly, all communication flows through a **Sovereign Cognitive Router (SCR)**:

```
reason://abc  ──→  SCR  ──→  best capable agent
```

The router considers:
- **Expertise**: capability match score
- **Trust**: reputation and attestation level
- **GPU locality**: KV-cache proximity, NVLink topology
- **Latency**: estimated response time
- **Jurisdiction**: data residency constraints
- **Capability grants**: active delegation tokens
- **Load**: current queue depth and utilization
- **Cost**: estimated compute expenditure

### 5.4 Cognitive Magnet Links

Objects are referenced by content-addressed pointers rather than copied:

```
mind://sha256:7a92...
session://sha256:def...
knowledge://sha256:abc...
reason://sha256:ff01...
```

A session can request `GET mind://7a92...` — if permitted, another node provides it. This enables portable, verifiable references across the federation.

### 5.5 Memory Graph

Rather than linear chat history, cognitive state is organized as a structured graph:

```
mind://enterprise
    ├── goals/
    ├── beliefs/
    ├── knowledge/
    ├── sessions/
    ├── evidence/
    ├── policies/
    ├── capabilities/
    └── world-model/
```

### 5.6 Hierarchical Minds

Minds can contain other minds, mirroring organizational structure:

```
mind://enterprise
    ├── mind://finance
    ├── mind://security
    ├── mind://research
    └── mind://operations
```

Each child mind can have its own constitution, policies, capabilities, memories, and goals. Parent minds delegate authority through capability tokens.

---

## 6. Cognitive Bus

All coordination is **event-driven**. The Cognitive Bus replaces synchronous agent-to-agent calls with an asynchronous event stream.

### 6.1 Event Taxonomy

| Category | Events |
|----------|--------|
| **Goal** | `goal.created`, `goal.updated`, `goal.completed`, `goal.failed` |
| **Reason** | `reason.started`, `reason.completed`, `reason.cached`, `reason.invalidated` |
| **Memory** | `memory.updated`, `memory.evicted`, `memory.synced` |
| **Policy** | `policy.validated`, `policy.denied`, `policy.updated` |
| **Capability** | `capability.granted`, `capability.revoked`, `capability.expired` |
| **Checkpoint** | `checkpoint.created`, `checkpoint.restored`, `checkpoint.failed` |
| **Scheduler** | `scheduler.dispatched`, `scheduler.preempted`, `scheduler.completed` |
| **Agent** | `agent.created`, `agent.started`, `agent.suspended`, `agent.terminated` |

### 6.2 Event Envelope

```json
{
  "event_type": "reason.completed",
  "uri": "reason://sha256:abc123",
  "timestamp": "2026-07-16T12:00:00Z",
  "source": "agent://reasoner-1",
  "session": "session://finance",
  "provenance": {
    "parent_event": "event://evt-042",
    "signature": "ed25519:..."
  },
  "payload": {}
}
```

---

## 7. Three-Tier Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 3 — GLOBAL BACKBONE                                   │
│  Geo-distributed Sovereign Sync Engine                      │
│  Cross-jurisdiction policy, civilizational knowledge        │
├─────────────────────────────────────────────────────────────┤
│  Tier 2 — REGIONAL MESH                                     │
│  Datacenter / zero-trust network                            │
│  Context sync, audit verification, governance checks        │
├─────────────────────────────────────────────────────────────┤
│  Tier 1 — LOCAL SUB-SWARM (Edge Mind)                       │
│  Shared NVLink / shared memory IPC                          │
│  Fast execution loops (code + compile, reason + verify)     │
└─────────────────────────────────────────────────────────────┘
```

### 7.1 Tier Communication

| From → To | Transport | Synchronization |
|-----------|-----------|-----------------|
| Tier 1 → Tier 1 | Shared memory / IPC | Real-time |
| Tier 1 → Tier 2 | gRPC / QUIC | Aggregated delta sync |
| Tier 2 → Tier 3 | Merkle-audit relays | State settlement |

---

## 8. Cognitive Economics

Resource allocation is formalized through resource contracts. The scheduler allocates resources based on policy, availability, and cost without prescribing a specific market mechanism.

| Resource URI | Purpose |
|-------------|---------|
| `compute://` | GPU/CPU allocation |
| `memory://` | Memory pool allocation |
| `bandwidth://` | Network capacity |
| `storage://` | Persistent storage |
| `energy://` | Power consumption budget |

---

## 9. Conformance

SIRA conformance is additive to the existing OASA conformance levels:

| Level | Requirement |
|-------|-------------|
| **SIRA-1 (Basic)** | Implements four-quadrant object model, basic URI addressing |
| **SIRA-2 (Cognitive)** | Implements Cognitive Router, Event Bus, Session isolation |
| **SIRA-3 (Federated)** | Implements three-tier topology, cross-node memory exchange |
| **SIRA-4 (Full)** | Implements Cognitive Economics, Hierarchical Minds, Multi-Agent Consensus |

---

## 10. Future Vision — The Cognitive Internet

```
┌──────────────────────────────────────────┐
│           GLOBAL FEDERATION              │
├──────────────────────────────────────────┤
│  Enterprise Minds · Government Minds     │
│  Research Minds · Personal Minds         │
│  Robot Minds                             │
├──────────────────────────────────────────┤
│  Shared Knowledge · Shared Evidence      │
│  Shared Policies · Shared Capabilities   │
├──────────────────────────────────────────┤
│  Sovereign Intelligence Protocols        │
├──────────────────────────────────────────┤
│           INFRASTRUCTURE                 │
└──────────────────────────────────────────┘
```

Instead of a network of chatbots, this is a network of collaborating cognitive systems. SIRA provides the common abstractions that allow diverse implementations to interoperate — just as TCP/IP, POSIX, and OCI have remained relevant across decades of technological change.

---

## References

- [OASA Compliance Framework](OASA.md)
- [Object Model](OBJECT_MODEL.md)
- [URI Standard](URI_STANDARD.md)
- [Protocol Registry](PROTOCOL_REGISTRY.md)
- [Constitution](CONSTITUTION.md)
- RFC-0060: Cognitive Mesh Architecture
- RFC-0061 through RFC-0069: Cognitive Protocol Family
