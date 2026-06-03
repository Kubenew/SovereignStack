# RFC-0036: Memory Fabric Objects

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Depends On:** RFC-0030

## Abstract

Extends the topology model from RFC-0030 to include memory pools as first-class fabric objects. Enables locality-aware memory allocation, tiered memory fabrics (HBM, DDR, CXL, remote), and memory-aware scheduling.

## Specification

### Memory Pool Object

```json
{
  "id": "mem://zcube-a/gpu-003/hbm",
  "type": "memory_pool",
  "tier": "hbm3",
  "node": "node://gpu-003",
  "capacity_gb": 80,
  "available_gb": 64,
  "bandwidth_gbps": 3500,
  "latency_ns": 80,
  "attributes": {
    "pooled": false,
    "cxl_enabled": false,
    "numa_node": 0
  }
}
```

### Memory Fabric Link

```json
{
  "id": "memlink://zcube-a/link-gpu003-hbm",
  "type": "memory_fabric_link",
  "source": "node://gpu-003",
  "target": "mem://zcube-a/gpu-003/hbm",
  "bandwidth_gbps": 3500,
  "latency_ns": 80
}
```

### Memory Topology

```json
{
  "id": "topology://zcube-a/memory",
  "type": "memory_topology",
  "pools": [
    {"id": "mem://zcube-a/gpu-003/hbm", "tier": "hbm3", "capacity_gb": 80},
    {"id": "mem://zcube-a/gpu-003/ddr", "tier": "ddr5", "capacity_gb": 512},
    {"id": "mem://pool-node-001/cxl", "tier": "cxl", "capacity_gb": 2048}
  ],
  "links": [
    {"source": "node://gpu-003", "target": "mem://zcube-a/gpu-003/hbm", "bandwidth_gbps": 3500},
    {"source": "node://gpu-003", "target": "mem://pool-node-001/cxl", "bandwidth_gbps": 64}
  ]
}
```

## Core Types

```rust
pub struct MemoryPool {
    pub id: String, pub tier: String, pub node: String,
    pub capacity_gb: u64, pub available_gb: u64,
    pub bandwidth_gbps: u64, pub latency_ns: u64,
}

pub struct MemoryFabricLink {
    pub source: String, pub target: String,
    pub bandwidth_gbps: u64, pub latency_ns: u64,
}

pub struct MemoryTopology {
    pub pools: Vec<MemoryPool>, pub links: Vec<MemoryFabricLink>,
}
```
