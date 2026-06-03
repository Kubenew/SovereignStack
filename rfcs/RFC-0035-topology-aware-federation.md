# RFC-0035: Topology-Aware Federation

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Depends On:** RFC-0030, RFC-0032, RFC-0008

## Abstract

Extends RFC-0008 Federation Routing with topology awareness from RFC-0030 and fabric operations from RFC-0032. Enables cross-fabric routing that accounts for inter-fabric gateway nodes, jurisdiction boundaries, and fabric cost gradients.

## Specification

### Cross-Fabric Route

```json
{
  "route_id": "fed-route-001",
  "source_node": "node://eu-cluster/gpu-001",
  "target_agent": "agent://us-researcher",
  "segments": [
    {"fabric": "fabric://eu-zcube", "hops": 2, "egress": "gateway://eu-frankfurt"},
    {"fabric": "fabric://transatlantic", "hops": 1, "egress": "gateway://us-ashburn"},
    {"fabric": "fabric://us-zcube", "hops": 3, "target": "agent://us-researcher"}
  ],
  "total_distance": 0.58,
  "jurisdictions": ["EU", "US"],
  "estimated_latency_ms": 85
}
```

### Gateway Node

```json
{
  "id": "gateway://eu-frankfurt",
  "type": "federation_gateway",
  "fabrics": ["fabric://eu-zcube", "fabric://transatlantic"],
  "jurisdictions": ["EU"],
  "attributes": {"bandwidth_gbps": 400, "latency_ms": 35}
}
```

### Federation Routing with Topology

When computing a cross-fabric route:

1. Resolve target agent's node via identity registry
2. Determine source and target fabrics
3. Find inter-fabric gateways
4. For each gateway pair, compute topology_distance across both fabrics
5. Add inter-gateway WAN cost (latency, bandwidth, jurisdiction compliance)
6. Return the path with lowest total cost

## Core Types

```rust
pub struct CrossFabricRoute {
    pub segments: Vec<FabricSegment>,
    pub total_distance: f64,
    pub jurisdictions: Vec<String>,
    pub estimated_latency_ms: u64,
}

pub struct FabricSegment {
    pub fabric: String, pub hops: u32,
    pub egress: Option<String>, pub target: Option<String>,
}

pub struct FederationGateway {
    pub id: String, pub fabrics: Vec<String>,
    pub jurisdictions: Vec<String>, pub bandwidth_gbps: u64,
}
```
