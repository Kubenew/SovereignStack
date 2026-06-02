# RFC-0030: Network Topology Awareness

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the topology model for AI fabrics in the SovereignStack ecosystem. Provides formal URI schemes, object schemas, and a distance-cost model for topology-aware scheduling. This is the foundation for RFC-0032 (AI Fabric Protocol) and RFC-0031 (KV Locality Scheduling).

## Motivation

Today's schedulers treat GPU count as the primary resource dimension. In practice, interconnect performance — fabric bandwidth, rail topology, leaf placement — increasingly dominates real-world inference and training throughput.

A scheduler that knows the topology can:

- Place decode near prefill (locality-aware)
- Avoid cross-rail hops for latency-sensitive operations
- Reserve contiguous fabric segments for collective operations
- Route around congested leaves or spines

This RFC formalises the topology as first-class sovereign objects so that every node, leaf, spine, and rail has a resolvable identity with measured attributes.

## Specification

### URI Schemes

RFC-0030 registers four new URI schemes in the SovereignStack registry:

```
leaf://      — A leaf switch or access-layer node
spine://     — A spine switch or aggregation-layer node
rail://      — A rail (one dimension of a multi-dimensional fabric)
fabric://    — A named fabric (collection of leaves, spines, rails)
topology://  — A named topology (cluster graph with nodes + links)
```

### Formal ABNF Grammar

```abnf
leaf-uri     = "leaf://" authority "/" leaf-id
leaf-id      = 1*( alpha / digit / "-" / "_" )

spine-uri    = "spine://" authority "/" spine-id
spine-id     = 1*( alpha / digit / "-" / "_" )

rail-uri     = "rail://" authority "/" rail-id
rail-id      = 1*( alpha / digit / "-" / "_" )

fabric-uri   = "fabric://" authority
              [ "/" segment ]

topology-uri = "topology://" authority
```

### Examples

```
leaf://fabric-a/leaf03
leaf://zcube-1/leaf03
spine://fabric-a/spine01
rail://fabric-a/rail7
fabric://zcube-a
fabric://zcube-a/partition-2
topology://cluster-prod
```

### Core Object Schemas

#### Leaf Object

```json
{
  "id": "leaf://fabric-a/leaf03",
  "type": "leaf",
  "fabric": "fabric://fabric-a",
  "attributes": {
    "bandwidth_gbps": 800,
    "latency_us": 2,
    "ports": 64,
    "utilization": 0.42
  },
  "location": {
    "rack": "rack-07",
    "row": "B"
  }
}
```

#### Spine Object

```json
{
  "id": "spine://fabric-a/spine01",
  "type": "spine",
  "fabric": "fabric://fabric-a",
  "attributes": {
    "bandwidth_gbps": 3200,
    "latency_us": 1,
    "ports": 128
  }
}
```

#### Rail Object

```json
{
  "id": "rail://fabric-a/rail7",
  "type": "rail",
  "fabric": "fabric://fabric-a",
  "attributes": {
    "dimension": 2,
    "bandwidth_gbps": 400,
    "latency_us": 3
  },
  "nodes": [
    "node://gpu-001",
    "node://gpu-009",
    "node://gpu-017",
    "node://gpu-025"
  ]
}
```

#### Fabric Object

```json
{
  "id": "fabric://zcube-a",
  "type": "fabric",
  "topology": "3d-torus",
  "dimensions": [4, 4, 4],
  "attributes": {
    "aggregate_bandwidth_gbps": 12800,
    "max_latency_us": 8,
    "min_latency_us": 1
  }
}
```

#### Topology Object

```json
{
  "id": "topology://cluster-prod",
  "type": "topology",
  "fabric": "fabric://zcube-a",
  "nodes": [
    {"id": "leaf://zcube-a/leaf01", "type": "leaf"},
    {"id": "leaf://zcube-a/leaf02", "type": "leaf"},
    {"id": "spine://zcube-a/spine01", "type": "spine"},
    {"id": "node://gpu-001", "type": "compute"},
    {"id": "node://gpu-064", "type": "compute"}
  ],
  "links": [
    {"source": "leaf://zcube-a/leaf01", "target": "spine://zcube-a/spine01", "bandwidth_gbps": 800, "latency_us": 2},
    {"source": "node://gpu-001", "target": "leaf://zcube-a/leaf01", "bandwidth_gbps": 400, "latency_us": 1},
    {"source": "node://gpu-064", "target": "leaf://zcube-a/leaf02", "bandwidth_gbps": 400, "latency_us": 1}
  ]
}
```

### Topology Group

A `topology_group` is a named set of compute nodes that share a common fabric leaf or rail. It is the unit of locality for scheduling decisions.

```json
{
  "id": "topology://zcube-1/group-a",
  "type": "topology_group",
  "fabric": "fabric://zcube-a",
  "nodes": ["node://gpu-001", "node://gpu-002", "node://gpu-003", "node://gpu-004"],
  "leaf": "leaf://zcube-a/leaf01",
  "locality_score": 0
}
```

Lower `locality_score` means tighter coupling (fewer fabric hops between nodes in the group).

### Topology-Aware Distance Model

Topology distance is the cost of moving data between two points in the fabric. It is a weighted composite of:

| Factor | Weight | Description |
|--------|--------|-------------|
| Hops | 0.4 | Number of fabric hops (leaf → spine → leaf) |
| Latency | 0.3 | Measured round-trip latency in microseconds |
| Bandwidth | 0.2 | Inverse of available bandwidth |
| Congestion | 0.1 | Current utilization of the path's bottleneck link |

```
distance(A, B) =
    0.4 * hops(A, B) / max_hops
  + 0.3 * latency_us(A, B) / max_latency
  + 0.2 * (1 - bandwidth_gbps(A, B) / max_bandwidth)
  + 0.1 * congestion(A, B)

locality_score = 1.0 - distance(normalized)
```

### Capability Registry Integration

Capability descriptors should include topology information so the registry can rank providers by proximity:

```json
{
  "provider": "agent://inference-node-7",
  "capability": "text_generation",
  "topology_group": "zcube-1/group-a",
  "kv_locality": "node://gpu-003",
  "accuracy": 0.97,
  "latency_ms": 120
}
```

When a consumer queries for `text_generation`, the registry ranks by a composite score:

```
rank_score =
    w_accuracy * accuracy
  + w_cost * (1 - normalized_cost)
  + w_latency * (1 - normalized_latency)
  + w_trust * trust_score
  - w_topology * topology_distance(consumer, provider)
  - w_kv * kv_transfer_cost(consumer, provider)
```

Default weights:

| Factor | Default Weight |
|--------|----------------|
| accuracy | 0.25 |
| cost | 0.10 |
| latency | 0.15 |
| trust | 0.10 |
| topology_distance | 0.25 |
| kv_transfer_cost | 0.15 |

## Reference Implementation

### Core Types

```rust
pub struct TopologyGroup {
    pub id: String,
    pub fabric: String,
    pub nodes: Vec<String>,
    pub leaf: Option<String>,
    pub locality_score: u32,
}

pub struct FabricLink {
    pub source: String,
    pub destination: String,
    pub bandwidth_gbps: u64,
    pub latency_us: u64,
}

pub struct MemoryLocality {
    pub source_node: String,
    pub target_node: String,
    pub cost: u32,
}
```

### URI Parsing

```rust
"leaf://fabric-a/leaf03"   → UriScheme::Leaf, authority: "fabric-a", path: "/leaf03"
"spine://fabric-a/spine01" → UriScheme::Spine, authority: "fabric-a", path: "/spine01"
"rail://fabric-a/rail7"    → UriScheme::Rail, authority: "fabric-a", path: "/rail7"
"fabric://zcube-a"         → UriScheme::Fabric, authority: "zcube-a"
"topology://cluster-prod"  → UriScheme::Topology, authority: "cluster-prod"
```

## Operations

### DISCOVER

List leaves, spines, rails, and nodes visible in a fabric.

```
GET /topology/discover?fabric=fabric://zcube-a
→ [leaf, spine, rail, node, link, ...]
```

### MEASURE

Probe one-shot or streaming latency and bandwidth between two points.

```
POST /topology/measure
{ "source": "leaf://zcube-a/leaf01", "target": "leaf://zcube-a/leaf02" }
→ { "latency_us": 3, "bandwidth_gbps": 780, "jitter_us": 0.5 }
```

### DISTANCE

Compute the topology distance between any two addressable points.

```
POST /topology/distance
{ "source": "node://gpu-001", "target": "node://gpu-032" }
→ { "distance": 0.37, "hops": 2, "latency_us": 5, "locality_score": 0.63 }
```

## Relationship to Other RFCs

| RFC | Dependency | Description |
|-----|------------|-------------|
| RFC-0001 | Base | Objects inherit the universal object model |
| RFC-0002 | Base | URI schemes registered in the scheme registry |
| RFC-0032 | Downstream | AI Fabric Protocol builds on topology objects |
| RFC-0031 | Downstream | KV Locality Scheduling uses distance model |
| RFC-0033 | Downstream | Fabric Telemetry streams MEASURE data |
| RFC-0034 | Downstream | Distributed KV Placement uses locality scores |

## Security Considerations

1. **Topology exposure** — Publishing fabric topology leaks cluster architecture. Access to `topology://` objects should be restricted to authenticated agents.
2. **Measurement injection** — MEASURE responses must be signed by the fabric to prevent spoofed latency/bandwidth data.
3. **Topology poisoning** — Malicious topology registrations could cause sub-optimal scheduling. Require attestation for fabric and node objects.

## Backward Compatibility

This RFC is additive. No existing URI schemes, object types, or protocols are modified. Existing `node://` URIs continue to work; topology information is optional metadata.

## Future Work

- RFC-0033 Fabric Telemetry Protocol — streaming MEASURE with push-based congestion events
- RFC-0034 Distributed KV Placement — placing KV caches on optimal rails
- RFC-0035 Topology-Aware Federation — routing sovereign requests across fabrics
- RFC-0036 Memory Fabric Objects — representing memory pools as fabric nodes
- RFC-0037 AI Cluster Profiles — named, versioned cluster configurations
