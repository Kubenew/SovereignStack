# RFC-0031: KV Locality Scheduling

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Authors:** SovereignStack Standards Committee
**Depends On:** RFC-0030, RFC-0032

## Abstract

Defines the KV Locality Scheduling model for the SovereignStack
ecosystem. Where RFC-0030 provides the topology model and RFC-0032
provides the fabric protocol, RFC-0031 defines *how* schedulers make
placement decisions that minimize KV cache transfer cost across the
fabric.

The core insight: for long-context inference, placing a decode
operation *near* its prefill's KV cache is often more impactful on
end-to-end latency than raw GPU throughput.

## Motivation

Current inference schedulers optimise for GPU-centric metrics: free
memory, compute capacity, queue depth. This works when KV cache
transfer time is negligible relative to compute time.

At scale — 128K+ context windows, 8+ GPU tensor-parallel inference,
multi-hop reasoning — KV cache transfer across fabric links
dominates latency:

| Scenario | Compute | KV Transfer | Fabric Hops | Total |
|----------|---------|-------------|-------------|-------|
| Local GPU, same leaf | 50ms | 2ms | 0 | 52ms |
| Same rail, 2 hops | 50ms | 18ms | 2 | 68ms |
| Cross-rail, 4 hops | 50ms | 45ms | 4 | 95ms |
| Cross-fabric, 6+ hops | 50ms | 120ms | 6+ | 170ms+ |

A locality-aware scheduler avoids the tail cases by treating KV cache
location as a first-class scheduling dimension alongside GPU capacity.

## Specification

### Architecture

```
Request
  │
  ▼
┌─────────────────────────────────┐
│         Scheduler               │
│                                 │
│  rank_score =                   │
│    w_gpu      * gpu_score       │
│  + w_capability * cap_score     │
│  + w_trust    * trust_score     │
│  - w_network  * network_cost    │
│  - w_kv       * kv_transfer_cost│
│                                 │
│  → Pick node with highest score │
└─────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────┐
│      Fabric Protocol (AFP)      │
│  RESERVE / ROUTE / MEASURE      │
└─────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────┐
│    Inference Runtime (node)     │
│  Load KV cache, run decode      │
└─────────────────────────────────┘
```

### KV Cache Object

A KV cache is a first-class sovereign object:

```json
{
  "id": "kv://zcube-a/gpu-003/session-abc/head-0",
  "type": "kv_cache",
  "owner": "session://abc",
  "node": "node://gpu-003",
  "model": "qwen2.5-72b",
  "layer": 0,
  "context_length": 65536,
  "precision": "fp8",
  "size_mb": 512,
  "created_at": "2026-06-02T12:00:00Z",
  "provenance": [
    {"action": "prefilled", "agent": "session://abc", "timestamp": "..."}
  ]
}
```

KV caches are discoverable via the node's object registry and their
location is published to the scheduler's locality index.

### Prefill-Decode Colocation

The central policy of RFC-0031:

> **A decode operation MUST be placed on the node closest to its
> prefill's KV cache, subject to compute capacity constraints.**

Formally, for each decode request:

1. Find the node(s) holding the relevant KV cache (from `kv://` objects)
2. For each candidate compute node, compute `kv_transfer_cost(node, cache_node)`
3. Filter candidates that cannot meet the latency budget
4. Rank remaining by composite score
5. Select the node with the highest score

### KV Transfer Cost Model

The cost of moving KV cache between two nodes is a function of:

| Factor | Symbol | Description |
|--------|--------|-------------|
| Cache size | `S` | Size of KV cache to transfer (MB) |
| Fabric distance | `D` | Topology distance between nodes (RFC-0030) |
| Available bandwidth | `B` | Min bandwidth along the path (RFC-0032 MEASURE) |
| Congestion | `C` | Current utilization of bottleneck link |

```
kv_transfer_cost(A, B) =
    w_size * (S / max_cache_size)
  + w_dist * D(A, B)
  + w_bw   * (1 - B_available / B_max)
  + w_cong * C(A, B)
```

Default weights:

| Factor | Weight | Description |
|--------|--------|-------------|
| Cache size | 0.30 | Larger caches cost more to transfer |
| Fabric distance | 0.35 | Topology distance (hops + latency) |
| Bandwidth | 0.20 | Available bandwidth on path |
| Congestion | 0.15 | Current bottleneck utilization |

### Composite Schedule Score

When ranking candidate nodes for placement, the scheduler computes:

```
schedule_score(node, request) =
    w_gpu        * gpu_capacity(node)
  + w_capability * capability_match(node, request)
  + w_trust      * trust_score(node)
  - w_network    * network_cost(node, request.source)
  - w_kv         * kv_transfer_cost(node, kv_cache_node)
  - w_latency    * estimated_latency(node, request)
```

#### Default Configuration

```json
{
  "scheduler": {
    "version": "1.0",
    "default_weights": {
      "gpu_capacity": 0.15,
      "capability":   0.15,
      "trust":        0.20,
      "network":      0.15,
      "kv_locality":  0.35
    },
    "prefill_decode_colocation": true,
    "kv_transfer_budget_ms": 20,
    "rebalance_interval_secs": 60
  }
}
```

The dominant weight is `kv_locality` (0.35), reflecting the
disproportionate impact of KV cache placement on end-to-end latency.

### Schedule Decision Flow

```
RECEIVE request
  │
  ├── 1. Parse request → extract model, context_length, session_id
  │
  ├── 2. Lookup KV cache location from session's kv:// objects
  │      via node registry
  │
  ├── 3. Candidate discovery:
  │      a. Query capability registry for matching capability
  │      b. Filter by trust threshold
  │      c. Filter by jurisdiction/policy (RFC-0009)
  │
  ├── 4. For each candidate node:
  │      a. Compute gpu_capacity (free memory, queue depth)
  │      b. Query AFP ROUTE for network_cost
  │      c. Query AFP MEASURE for kv_transfer_cost
  │      d. Compute composite schedule_score
  │
  ├── 5. Select node with highest score
  │
  ├── 6. If prefill_decode_colocation:
  │      a. If this is a decode for existing prefill:
  │         → Prefer KV cache node unless capacity exhausted
  │      b. If this is a new prefill:
  │         → Consider future decode locality when placing prefill
  │
  └── 7. Submit placement decision to orchestrator
```

### Nodeside KV Locality Index

Each node maintains a locality index — a map of known KV cache
locations ordered by fabric distance from this node:

```json
{
  "node_id": "node://gpu-007",
  "local_kv_caches": [
    {"id": "kv://zcube-a/gpu-007/session-abc/head-0", "size_mb": 512, "status": "resident"},
    {"id": "kv://zcube-a/gpu-007/session-def/head-0", "size_mb": 256, "status": "resident"}
  ],
  "nearest_kv_caches": [
    {"node": "node://gpu-008", "distance": 0.12, "cache_count": 3},
    {"node": "node://gpu-015", "distance": 0.24, "cache_count": 1},
    {"node": "node://gpu-032", "distance": 0.37, "cache_count": 5}
  ]
}
```

### Cluster-Wide KV Placement Optimiser

An optional cluster-level component that periodically rebalances KV
cache placement to minimise expected transfer costs:

```json
{
  "operation": "optimise_kv_placement",
  "objective": "minimise_weighted_transfer_cost",
  "constraints": {
    "max_cache_per_node_mb": 4096,
    "min_free_memory_gb": 16,
    "rebalance_threshold": 0.85
  }
}
```

The optimiser uses a greedy assignment: for each active session,
place its KV cache on the node that minimises the sum of weighted
distances to all decode nodes expected to serve that session.

## Reference Implementation

### Core Types

```rust
/// A KV cache location known to the scheduler.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVCachePlacement {
    pub cache_id: String,
    pub node_id: String,
    pub session_id: String,
    pub model: String,
    pub layer: u32,
    pub context_length: u32,
    pub size_mb: u64,
    pub created_at: Timestamp,
}

/// The composite locality score between two nodes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalityScore {
    pub source_node: String,
    pub target_node: String,
    pub topology_distance: f64,
    pub kv_transfer_cost: f64,
    pub network_cost: f64,
    pub composite_score: f64,
}

/// A single schedule ranking for a candidate node.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleRank {
    pub node_id: String,
    pub gpu_score: f64,
    pub capability_score: f64,
    pub trust_score: f64,
    pub network_cost: f64,
    pub kv_transfer_cost: f64,
    pub composite_score: f64,
}

/// Scheduler configuration with tunable weights.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulerConfig {
    pub gpu_capacity_weight: f64,
    pub capability_weight: f64,
    pub trust_weight: f64,
    pub network_weight: f64,
    pub kv_locality_weight: f64,
    pub prefill_decode_colocation: bool,
    pub kv_transfer_budget_ms: u64,
}

impl Default for SchedulerConfig {
    fn default() -> Self {
        Self {
            gpu_capacity_weight: 0.15,
            capability_weight: 0.15,
            trust_weight: 0.20,
            network_weight: 0.15,
            kv_locality_weight: 0.35,
            prefill_decode_colocation: true,
            kv_transfer_budget_ms: 20,
        }
    }
}
```

### Scheduler Trait

```rust
#[async_trait]
pub trait LocalityScheduler: Send + Sync {
    /// Rank candidate nodes for a given request.
    async fn rank_candidates(
        &self,
        request: &ScheduleRequest,
        candidates: &[CandidateNode],
    ) -> Vec<ScheduleRank>;

    /// Select the best node for a request.
    async fn schedule(
        &self,
        request: &ScheduleRequest,
    ) -> Result<ScheduleRank, ScheduleError>;

    /// Rebalance KV cache placement across the cluster.
    async fn rebalance_kv(
        &self,
    ) -> Result<KVPlacementPlan, ScheduleError>;
}
```

## Integration with RFC-0030 and RFC-0032

| RFC | Type / Operation | Used For |
|-----|------------------|----------|
| RFC-0030 | `TopologyGroup` | Determining which nodes share a leaf/rail |
| RFC-0030 | `FabricLink` | Path segments for cost calculation |
| RFC-0030 | `distance(A, B)` | Computing topology_distance in LocalityScore |
| RFC-0032 | AFP MEASURE | Probing available bandwidth for kv_transfer_cost |
| RFC-0032 | AFP ROUTE | Computing network_cost between candidates |
| RFC-0032 | AFP RESERVE | Reserving fabric segments for KV transfer |

## Security Considerations

1. **KV cache snooping** — KV caches contain the full context of a
   session (prompt + reasoning). Access to `kv://` objects must be
   restricted to authenticated agents belonging to the same session.
2. **Placement poisoning** — A malicious node could advertise zero
   kv_transfer_cost to attract decode traffic. Schedulers should
   verify cost claims via independent AFP MEASURE probes.
3. **Session isolation** — KV caches from different sessions must
   not share physical memory. Enforce via node-level memory isolation.
4. **Rebalance interference** — Moving KV caches during active
   inference can cause latency spikes. Rebalance operations should
   be scheduled during low-utilization windows or use live migration
   with connection draining.

## Relationship to Other RFCs

| RFC | Dependency | Description |
|-----|------------|-------------|
| RFC-0001 | Base | KV cache objects inherit universal model |
| RFC-0002 | Base | kv:// URI scheme in the registry (future) |
| RFC-0004 | Integration | Capability registry ranking includes locality |
| RFC-0030 | Required | Topology model + distance function |
| RFC-0032 | Required | Fabric operations for MEASURE/ROUTE/RESERVE |
| RFC-0033 | Future | Fabric Telemetry for real-time congestion |
| RFC-0034 | Future | Distributed KV Placement using this model |

## Backward Compatibility

This RFC is additive. Existing schedulers that ignore locality
continue to work but will produce sub-optimal placements.

The `kv_locality_weight` defaults to 0.0 for backward-compatible
configurations and to 0.35 for new deployments.

## Future Work

- RFC-0034 Distributed KV Placement — cluster-wide KV cache
  placement optimiser using the cost model from this RFC
- RFC-0036 Memory Fabric Objects — representing KV caches as
  first-class fabric objects with measured locality
- Live KV migration — moving KV caches between nodes during
  active inference with zero-downtime
- Predictive pre-placement — prefetching KV caches onto likely
  decode nodes based on session history
