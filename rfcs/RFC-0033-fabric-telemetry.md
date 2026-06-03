# RFC-0033: Fabric Telemetry Protocol

**Status:** Draft
**Type:** Standard
**Created:** 2026-06-02
**Depends On:** RFC-0032

## Abstract

Defines the Fabric Telemetry Protocol (FTP) for streaming real-time congestion, latency, bandwidth, and health data from fabric elements. Extends RFC-0032's streaming MEASURE with push-based events, threshold alerts, and historical telemetry queries.

## Specification

### Telemetry Event

```json
{
  "id": "tel://zcube-a/evt-001",
  "source": "leaf://zcube-a/leaf03",
  "event_type": "congestion.spike",
  "severity": "warning",
  "timestamp": "2026-06-02T12:00:00Z",
  "metrics": {
    "congestion": 0.87,
    "buffer_occupancy_pct": 72,
    "drop_rate": 0.0003
  },
  "ttl_secs": 300
}
```

### Threshold Rule

```json
{
  "id": "rule-001",
  "metric": "congestion",
  "operator": ">",
  "value": 0.80,
  "duration_secs": 5,
  "actions": ["alert", "log", "reroute_hint"]
}
```

### Telemetry Stream

WebSocket endpoint at `ws://host:port/afp/v1/telemetry` accepting:

```json
{
  "subscribe": {
    "sources": ["leaf://zcube-a/leaf03", "spine://zcube-a/spine01"],
    "metrics": ["congestion", "bandwidth_utilization", "drop_rate"],
    "interval_ms": 1000
  }
}
```

## Core Types

```rust
pub struct TelemetryEvent {
    pub id: String, pub source: String, pub event_type: String,
    pub severity: String, pub timestamp: Timestamp,
    pub metrics: HashMap<String, f64>, pub ttl_secs: u64,
}

pub struct ThresholdRule {
    pub id: String, pub metric: String, pub operator: String,
    pub value: f64, pub duration_secs: u64, pub actions: Vec<String>,
}

pub struct TelemetrySubscription {
    pub sources: Vec<String>, pub metrics: Vec<String>, pub interval_ms: u64,
}
```
