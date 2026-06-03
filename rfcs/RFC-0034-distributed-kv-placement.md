# RFC-0034: Distributed KV Placement

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Depends On:** RFC-0031, RFC-0032

## Abstract

Defines the cluster-wide KV cache placement optimiser that uses the cost model from RFC-0031 and the fabric operations from RFC-0032 to minimise weighted KV transfer cost across all active sessions.

## Specification

### Placement Plan

```json
{
  "operation": "kv_placement",
  "objective": "minimise_weighted_transfer_cost",
  "sessions": [
    {"session_id": "session://abc", "cache_size_mb": 512,
     "preferred_nodes": ["node://gpu-003", "node://gpu-007"],
     "current_node": "node://gpu-003"}
  ],
  "assignments": [
    {"cache_id": "kv://zcube-a/gpu-003/session-abc/head-0",
     "assigned_node": "node://gpu-003",
     "cost": 0.05}
  ]
}
```

### Optimiser Algorithm

```
1. Collect all active sessions and their KV cache sizes
2. For each session, compute expected decode traffic pattern
3. For each candidate node, compute weighted transfer cost:
   cost(session, node) = sum over decode_nodes of
     frequency(decode_node) * kv_transfer_cost(node, decode_node)
4. Assign each session to the node with minimum cost
5. Enforce per-node capacity constraint (max_cache_per_node_mb)
6. Generate migration plan for caches that must move
```

### Migration Operation

```json
{
  "migration_id": "mig-001",
  "cache_id": "kv://zcube-a/gpu-003/session-abc/head-0",
  "from": "node://gpu-003",
  "to": "node://gpu-015",
  "size_mb": 512,
  "strategy": "live_migrate",
  "estimated_duration_secs": 30,
  "lease_token": "token:ed25519:..."
}
```

## Core Types

```rust
pub struct KVPlacementPlan {
    pub sessions: Vec<KVSessionAssignment>,
    pub migrations: Vec<KVCacheMigration>,
    pub total_cost_reduction: f64,
}

pub struct KVSessionAssignment {
    pub session_id: String, pub cache_size_mb: u64,
    pub assigned_node: String, pub cost: f64,
}

pub struct KVCacheMigration {
    pub cache_id: String, pub from_node: String, pub to_node: String,
    pub size_mb: u64, pub strategy: String,
}
```
