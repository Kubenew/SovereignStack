# RFC-0037: AI Cluster Profiles

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Depends On:** RFC-0030, RFC-0031, RFC-0036

## Abstract

Defines named, versioned AI cluster profiles that capture the full topology, fabric, memory, and scheduling configuration of a SovereignStack cluster. Enables portable, reproducible cluster definitions that can be shared, versioned, and validated across deployments.

## Specification

### Cluster Profile

```json
{
  "id": "profile://zcube-standard-v1",
  "name": "ZCube Standard 64-GPU",
  "version": "1.0.0",
  "created": "2026-06-02T12:00:00Z",
  "topology": {
    "fabric": "fabric://zcube-a",
    "dimensions": [4, 4, 4],
    "nodes": 64,
    "gpus_per_node": 8,
    "topology_group": "zcube-1"
  },
  "fabric": {
    "leaf_bandwidth_gbps": 800,
    "spine_bandwidth_gbps": 3200,
    "rail_count": 8,
    "inter_rail_latency_us": 5,
    "intra_rail_latency_us": 1
  },
  "memory": {
    "hbm_per_gpu_gb": 80,
    "hbm_bandwidth_gbps": 3500,
    "ddr_per_node_gb": 512,
    "cxl_pool_gb": 2048
  },
  "scheduler": {
    "kv_locality_weight": 0.35,
    "trust_weight": 0.20,
    "latency_weight": 0.20,
    "cost_weight": 0.10,
    "capability_weight": 0.15
  },
  "validation": {
    "min_conformant_rfcs": ["0030", "0031", "0032", "0036"],
    "required_conformance_level": "L2"
  }
}
```

### Profile Registry

Profiles are stored as sovereign objects (`profile://`) and registered in a profile registry:

```json
{
  "operation": "register_profile",
  "profile_id": "profile://zcube-standard-v1",
  "signature": "sig:ed25519:base64..."
}
```

### Profile Resolution

```json
{
  "operation": "resolve_profile",
  "query": {"gpu_count": 64, "min_hbm_gb": 80, "fabric": "3d-torus"},
  "top_k": 3
}
```

## Core Types

```rust
pub struct ClusterProfile {
    pub id: String, pub name: String, pub version: String,
    pub topology: ClusterTopology, pub fabric: ClusterFabricSpec,
    pub memory: ClusterMemorySpec, pub scheduler: SchedulerConfig,
}

pub struct ClusterTopology {
    pub fabric: String, pub dimensions: Vec<u32>,
    pub nodes: u32, pub gpus_per_node: u32,
}

pub struct ClusterFabricSpec {
    pub leaf_bandwidth_gbps: u64, pub spine_bandwidth_gbps: u64,
    pub rail_count: u32,
    pub inter_rail_latency_us: u64, pub intra_rail_latency_us: u64,
}

pub struct ClusterMemorySpec {
    pub hbm_per_gpu_gb: u64, pub hbm_bandwidth_gbps: u64,
    pub ddr_per_node_gb: u64, pub cxl_pool_gb: u64,
}
```
