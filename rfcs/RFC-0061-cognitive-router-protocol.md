# RFC-0061: Cognitive Router Protocol (CRP)

**Status:** Draft | **Type:** Standard | **Created:** 2026-07-16 | **Depends On:** RFC-0001, RFC-0024, RFC-0060  
**Protocol ID:** CRP

## Abstract

Defines the Sovereign Cognitive Router (SCR) — a semantic routing layer that resolves cognitive requests to the optimal executing agent or model based on capability, trust, locality, jurisdiction, and cost. Replaces static DNS/REST-based service discovery with content-aware, policy-governed routing.

## Motivation

Traditional service routing (DNS → IP → Port) is insufficient for cognitive workloads. The Cognitive Router resolves requests using:

- **Semantic matching** — route by capability, not by address
- **Trust scoring** — prefer agents with higher reputation
- **GPU topology awareness** — minimize data movement
- **Jurisdiction compliance** — enforce data residency
- **Economic optimization** — minimize compute cost

## Terminology

| Term | Definition |
|------|------------|
| **SCR** | Sovereign Cognitive Router — the routing component |
| **Semantic Anycast** | Resolving a capability URI to the best available provider |
| **KV Pointer** | A content-addressed reference to a KV cache (`kv://sha256:...`) |
| **Cognitive Magnet Link** | A portable, content-addressed reference to any cognitive object |
| **Routing Score** | Composite score used to select the best provider |

## Specification

### 1. Semantic Anycast

When an agent needs a capability, it addresses the request to a **semantic capability URI** rather than a specific endpoint:

```
agent://reasoning/math        → resolves to best math reasoning provider
agent://vision/detection       → resolves to best vision model
agent://planning/strategic     → resolves to best planning agent
agent://robotics/navigation    → resolves to best navigation model
```

The router resolves the best provider using the scoring function defined in §4.

### 2. Routing Request

```json
{
  "request_id": "req-001",
  "source": "agent://planner-1",
  "target_capability": "agent://reasoning/math",
  "session": "session://finance",
  "constraints": {
    "max_latency_ms": 500,
    "max_cost": 0.01,
    "jurisdiction": "EU",
    "min_trust_score": 0.8
  },
  "context_pointer": "kv://sha256:7a92ff01...",
  "payload_hash": "sha256:abc123..."
}
```

### 3. Routing Response

```json
{
  "request_id": "req-001",
  "resolved_to": "agent://reasoner-eu-3",
  "node": "node://eu-frankfurt-1",
  "routing_score": 0.92,
  "estimated_latency_ms": 120,
  "estimated_cost": 0.003,
  "kv_cache_hit": true,
  "capability_grant": "capability://temp-grant-001"
}
```

### 4. Scoring Function

The router computes a composite routing score:

```
score = w_capability × capability_match
      + w_trust      × trust_score
      + w_latency    × (1 - normalized_latency)
      + w_locality   × gpu_locality_score
      + w_jurisdiction × jurisdiction_match
      + w_load       × (1 - normalized_load)
      + w_cost       × (1 - normalized_cost)
      + w_kv_cache   × kv_cache_proximity
```

Default weights:

| Weight | Default | Description |
|--------|---------|-------------|
| `w_capability` | 0.25 | Capability match quality |
| `w_trust` | 0.15 | Provider reputation |
| `w_latency` | 0.15 | Estimated response time |
| `w_locality` | 0.10 | GPU/memory topology proximity |
| `w_jurisdiction` | 0.10 | Jurisdiction compliance (binary: 0 or 1) |
| `w_load` | 0.10 | Current queue depth |
| `w_cost` | 0.10 | Estimated compute cost |
| `w_kv_cache` | 0.05 | KV cache co-location bonus |

Weights are configurable per deployment via `policy://routing-weights`.

### 5. KV Pointer Passing

Instead of sending full context (potentially 50k+ tokens), the router passes only a content-addressed pointer:

```
kv://sha256:7a92ff01...
```

The target node pulls only the missing delta activation blocks or leverages shared host memory (NVLink/HBM). This can reduce network serialization overhead by up to 90%.

Pointer passing applies to all content-addressed objects:

| Object | Pointer Example |
|--------|----------------|
| KV Cache | `kv://sha256:7a92ff01...` |
| Memory | `memory://sha256:abc123...` |
| Knowledge | `knowledge://sha256:def456...` |
| Reasoning | `reason://sha256:ff01ab...` |
| Checkpoint | `checkpoint://sha256:99ee...` |

### 6. Cognitive Magnet Links

Any cognitive object can be referenced as a portable magnet link:

```
mind://sha256:7a92ff01...
session://sha256:def456...
knowledge://sha256:abc123...
reason://sha256:ff01ab...
```

These are content-addressed, verifiable, and portable across the federation. A node receiving a magnet link can:

1. Check local cache
2. Query regional mesh peers
3. Query global federation (if permitted by jurisdiction policy)

### 7. Fallback Semantics

```
Local node → Regional mesh → Global federation
```

1. If a local engine matches the capability, route locally (lowest latency).
2. If no local match, query the regional mesh via gossip discovery.
3. If no regional match, broadcast a compute request to the global federation via `ss-economy`.
4. If all fail, return `503 — Capability Unavailable`.

### 8. State Machine

```
IDLE → RESOLVING → DISPATCHING → AWAITING → COMPLETE
                 ↘ FALLBACK_REGIONAL → FALLBACK_GLOBAL
                                     ↘ FAILED
```

## Core Types

```rust
pub struct RoutingRequest {
    pub request_id: String,
    pub source: SovereignUri,
    pub target_capability: SovereignUri,
    pub session: SovereignUri,
    pub constraints: RoutingConstraints,
    pub context_pointer: Option<String>,
}

pub struct RoutingConstraints {
    pub max_latency_ms: Option<u64>,
    pub max_cost: Option<f64>,
    pub jurisdiction: Option<String>,
    pub min_trust_score: Option<f64>,
}

pub struct RoutingResult {
    pub resolved_to: SovereignUri,
    pub node: SovereignUri,
    pub routing_score: f64,
    pub estimated_latency_ms: u64,
    pub estimated_cost: f64,
    pub kv_cache_hit: bool,
}

pub struct RoutingWeights {
    pub capability: f64,
    pub trust: f64,
    pub latency: f64,
    pub locality: f64,
    pub jurisdiction: f64,
    pub load: f64,
    pub cost: f64,
    pub kv_cache: f64,
}
```

## Security Considerations

- Routing requests MUST be authenticated via the source agent's identity
- Routing MUST enforce jurisdiction constraints — a request with `jurisdiction: "EU"` MUST NOT be routed to a non-EU node
- KV pointer resolution MUST verify capability grants before serving cached data
- Routing scores MUST NOT be influenced by untrusted external signals

## Conformance Impact

- Required for **SIRA-2** conformance
- Extends RFC-0024 (Multi-Model Routing) with cognitive-aware scoring
- Reference implementation: `ss-routing/`
