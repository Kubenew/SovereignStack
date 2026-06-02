# RFC-0032: AI Fabric Protocol

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Authors:** SovereignStack Standards Committee
**Depends On:** RFC-0030 (Network Topology Awareness)

## Abstract

Defines the AI Fabric Protocol (AFP) for discovering, measuring,
reserving, and routing across AI fabrics. Where RFC-0030 provides the
static topology model, RFC-0032 defines the active protocol layer that
schedulers, orchestrators, and inference runtimes use to interact with
the fabric in real time.

## Motivation

AI fabrics (NVLink domains, Ultra Ethernet fabrics, InfiniBand subnets,
3D torus interconnects) are not passive infrastructure. They have
dynamic state — congestion, available bandwidth, active reservations,
fault domains — that directly impacts scheduling quality.

Without a fabric protocol, schedulers must guess or probe indirectly,
leading to sub-optimal placement, tail latency, and collective
operation contention.

AFP provides a standardised interface for:

- **DISCOVER** — enumerate topology elements visible through the fabric
- **MEASURE** — probe one-shot or streaming latency/bandwidth between
  any two addressable endpoints
- **RESERVE** — lease a fabric segment (path + bandwidth) for the
  duration of a collective operation
- **ROUTE** — compute an optimal path between source and target given
  current fabric state and constraints

## Specification

### URI Scheme

RFC-0032 registers one new URI scheme in addition to those from
RFC-0030:

```
link://     — A named, measured link between two topology elements
```

#### Formal ABNF

```abnf
link-uri     = "link://" authority "/" link-id
link-id      = 1*( alpha / digit / "-" / "_" )
```

#### Examples

```
link://zcube-a/link-leaf01-spine01
link://zcube-a/link-gpu001-leaf01
link://fabric-b/rail3-uplink
```

### Protocol Operations

All operations use a request-response message format over a reliable
transport (WebSocket or HTTPS). Messages are JSON objects with a
common envelope.

#### Common Envelope

```json
{
  "protocol": "afp",
  "version": "1.0",
  "request_id": "uuid",
  "timestamp": "2026-06-02T12:00:00Z",
  "authenticator": "sig:ed25519:base64..."
}
```

Every response includes the same envelope with an additional `status`
field.

---

### 1. DISCOVER

Enumerate topology elements visible through a fabric.

#### Request

```json
{
  "fabric": "fabric://zcube-a",
  "types": ["leaf", "spine", "rail", "link", "node"],
  "filters": {
    "rack": "rack-07",
    "status": "healthy"
  }
}
```

#### Response

```json
{
  "elements": [
    {"id": "leaf://zcube-a/leaf01", "type": "leaf", "status": "healthy",
     "attributes": {"ports": 64, "utilization": 0.42}},
    {"id": "spine://zcube-a/spine01", "type": "spine", "status": "healthy",
     "attributes": {"ports": 128, "utilization": 0.38}},
    {"id": "link://zcube-a/link-leaf01-spine01", "type": "link", "status": "healthy",
     "attributes": {"bandwidth_gbps": 800, "latency_us": 2, "congestion": 0.15}},
    {"id": "node://gpu-001", "type": "compute", "status": "healthy",
     "attributes": {"gpu_count": 8, "memory_gb": 80}}
  ],
  "count": 4,
  "discovered_at": "2026-06-02T12:00:01Z"
}
```

---

### 2. MEASURE

Probe latency and bandwidth between two endpoints. Supports both
one-shot and streaming (push-based telemetry) modes.

#### Request (one-shot)

```json
{
  "measurement_id": "m-001",
  "source": "link://zcube-a/link-gpu001-leaf01",
  "target": "link://zcube-a/link-gpu064-leaf02",
  "mode": "oneshot",
  "samples": 100
}
```

#### Response (one-shot)

```json
{
  "measurement_id": "m-001",
  "source": "link://zcube-a/link-gpu001-leaf01",
  "target": "link://zcube-a/link-gpu064-leaf02",
  "latency_us": {"min": 2.1, "avg": 2.4, "max": 3.8, "p99": 3.2},
  "bandwidth_gbps": {"min": 760, "avg": 785, "max": 800, "p99": 795},
  "jitter_us": 0.5,
  "packet_loss": 0.0001,
  "measured_at": "2026-06-02T12:00:05Z"
}
```

#### Request (streaming)

```json
{
  "measurement_id": "m-002",
  "source": "node://gpu-001",
  "target": "node://gpu-064",
  "mode": "stream",
  "interval_ms": 1000,
  "duration_secs": 60
}
```

#### Response (streaming)

A series of telemetry events delivered over the same connection:

```json
{"measurement_id": "m-002", "seq": 1, "latency_us": 2.3, "bandwidth_gbps": 790, "timestamp": "..."}
{"measurement_id": "m-002", "seq": 2, "latency_us": 2.5, "bandwidth_gbps": 782, "timestamp": "..."}
...
```

---

### 3. RESERVE

Lease a fabric segment (path + bandwidth) for a collective operation.
Reservations are time-bound and must be renewed or released.

#### Request

```json
{
  "reservation_id": "r-001",
  "fabric": "fabric://zcube-a",
  "type": "collective",
  "collective": "all_reduce",
  "participants": [
    "node://gpu-001", "node://gpu-002",
    "node://gpu-003", "node://gpu-004"
  ],
  "bandwidth_gbps": 400,
  "duration_secs": 300,
  "traffic_class": "low_latency",
  "topology_hint": {
    "preferred_leaf": "leaf://zcube-a/leaf01",
    "require_shared_rail": true
  }
}
```

#### Response

```json
{
  "reservation_id": "r-001",
  "status": "confirmed",
  "path": {
    "segments": [
      {"from": "node://gpu-001", "to": "leaf://zcube-a/leaf01", "via": "link://zcube-a/link-gpu001-leaf01"},
      {"from": "leaf://zcube-a/leaf01", "to": "spine://zcube-a/spine01", "via": "link://zcube-a/link-leaf01-spine01"},
      {"from": "spine://zcube-a/spine01", "to": "leaf://zcube-a/leaf01", "via": "link://zcube-a/link-spine01-leaf01"},
      {"from": "leaf://zcube-a/leaf01", "to": "node://gpu-002", "via": "link://zcube-a/link-leaf01-gpu002"}
    ]
  },
  "allocated_bandwidth_gbps": 400,
  "expires_at": "2026-06-02T12:05:00Z",
  "lease_token": "token:ed25519:base64..."
}
```

#### Release

```json
{
  "reservation_id": "r-001",
  "operation": "release",
  "lease_token": "token:ed25519:base64..."
}
```

---

### 4. ROUTE

Compute an optimal path between source and target given current fabric
state and scheduling constraints.

#### Request

```json
{
  "route_id": "path-001",
  "fabric": "fabric://zcube-a",
  "source": "node://gpu-001",
  "target": "node://gpu-117",
  "constraints": {
    "max_hops": 4,
    "max_latency_us": 10,
    "min_bandwidth_gbps": 100,
    "avoid_nodes": ["node://gpu-050"],
    "traffic_class": "best_effort"
  },
  "optimization": "latency"
}
```

#### Response

```json
{
  "route_id": "path-001",
  "status": "found",
  "path": {
    "hops": [
      {"node": "node://gpu-001", "egress": "link://zcube-a/link-gpu001-leaf01"},
      {"node": "leaf://zcube-a/leaf01", "egress": "link://zcube-a/link-leaf01-spine03"},
      {"node": "spine://zcube-a/spine03", "egress": "link://zcube-a/link-spine03-leaf07"},
      {"node": "leaf://zcube-a/leaf07", "egress": "link://zcube-a/link-leaf07-gpu117"},
      {"node": "node://gpu-117"}
    ]
  },
  "metrics": {
    "total_hops": 4,
    "estimated_latency_us": 7,
    "available_bandwidth_gbps": 400
  },
  "computed_at": "2026-06-02T12:00:10Z"
}
```

### Traffic Classes

| Class | Priority | Use Case |
|-------|----------|----------|
| `low_latency` | 1 | Inference, real-time agent communication |
| `collective` | 2 | All-reduce, all-gather (training) |
| `bulk_data` | 3 | Checkpointing, model transfer |
| `best_effort` | 4 | Telemetry, logging, non-critical traffic |

### Lease Token

Reservations return a lease token — a cryptographic signature over
the reservation parameters that the holder presents to prove
entitlement. Tokens have the format:

```
token:{algorithm}:{base64-signature}
```

The token must be presented for RESERVE/RELEASE operations and can
be verified by the fabric controller without consulting a central
database.

### Protocol State Machine

```
IDLE
  │
  ├── DISCOVER → DISCOVERED
  │
  ├── MEASURE → MEASURED
  │
  ├── ROUTE → ROUTE_COMPUTED
  │
  └── RESERVE → RESERVED
                  │
                  ├── RENEW → RESERVED (extended)
                  │
                  └── RELEASE → IDLE
```

## Reference Implementation

### Core Types

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricRoute {
    pub source: String,
    pub target: String,
    pub hops: Vec<FabricHop>,
    pub estimated_latency_us: u64,
    pub available_bandwidth_gbps: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricHop {
    pub node: String,
    pub egress_link: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricReservation {
    pub id: String,
    pub fabric: String,
    pub collective: Option<String>,
    pub participants: Vec<String>,
    pub allocated_bandwidth_gbps: u64,
    pub expires_at: String,
    pub lease_token: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricMeasurement {
    pub source: String,
    pub target: String,
    pub latency_us: LatencyStats,
    pub bandwidth_gbps: BandwidthStats,
    pub measured_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatencyStats {
    pub min: f64,
    pub avg: f64,
    pub max: f64,
    pub p99: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BandwidthStats {
    pub min: u64,
    pub avg: u64,
    pub max: u64,
    pub p99: u64,
}
```

### AFP Client Interface

```rust
#[async_trait]
pub trait FabricProtocol: Send + Sync {
    /// Discover topology elements visible through the fabric.
    async fn discover(&self, fabric: &str, types: &[&str])
        -> Result<Vec<TopologyElement>, FabricError>;

    /// Measure latency and bandwidth between two endpoints.
    async fn measure(&self, source: &str, target: &str, samples: u32)
        -> Result<FabricMeasurement, FabricError>;

    /// Reserve a fabric segment for a collective operation.
    async fn reserve(&self, req: &ReservationRequest)
        -> Result<FabricReservation, FabricError>;

    /// Release a reservation.
    async fn release(&self, reservation_id: &str, token: &str)
        -> Result<(), FabricError>;

    /// Compute an optimal path between source and target.
    async fn route(&self, req: &RouteRequest)
        -> Result<FabricRoute, FabricError>;
}
```

## Integration with RFC-0030

RFC-0032 depends on RFC-0030 for its type system:

| RFC-0030 Type | Used In |
|---------------|---------|
| `TopologyGroup` | RESERVE topology_hint |
| `FabricLink` | DISCOVER response, ROUTE hop egress |
| `MemoryLocality` | ROUTE constraint evaluation |

The DISCOVER operation from RFC-0032 is the active counterpart to
RFC-0030's static topology objects — DISCOVER returns live state
(utilization, congestion, health) while RFC-0030 provides the
structural schema.

## Security Considerations

1. **Lease token integrity** — Tokens must be signed by the fabric
   controller's Ed25519 key. Tokens presented to RELEASE must match
   the original reservation parameters (participants, bandwidth,
   duration) to prevent replay or escalation.
2. **Measurement injection** — MEASURE responses should be signed so
   that schedulers can verify fabric state authenticity. Unsigned
   measurements must be treated as untrusted.
3. **Reservation exhaustion** — A malicious agent could reserve all
   available bandwidth. Implement per-agent reservation quotas and
   TTL-based automatic release.
4. **Topology enumeration** — DISCOVER responses may reveal cluster
   topology. Access to AFP endpoints should require valid agent
   identity and authentication.

## Relationship to Other RFCs

| RFC | Dependency | Description |
|-----|------------|-------------|
| RFC-0001 | Base | Objects inherit the universal object model |
| RFC-0002 | Base | URI schemes registered in the scheme registry |
| RFC-0030 | Required | Topology model, distance function, types |
| RFC-0031 | Downstream | KV Locality Scheduling uses ROUTE + MEASURE |
| RFC-0033 | Downstream | Fabric Telemetry builds on streaming MEASURE |

## Backward Compatibility

This RFC is additive. It introduces no changes to existing URI schemes,
object types, or protocols. The AFP operates alongside existing
SovereignStack protocols as a specialised fabric interface.

## Future Work

- RFC-0033 Fabric Telemetry Protocol — push-based congestion events,
  streaming telemetry with threshold alerts
- RFC-0034 Distributed KV Placement — using RESERVE to pin KV caches
  on optimal rails
- RFC-0035 Topology-Aware Federation — routing sovereign requests
  across fabrics using ROUTE
- Multi-fabric routing — ROUTE across multiple fabrics with
  gateway leaf nodes
- Fabric health prognosis — predictive rerouting based on
  telemetry trends
