# RFC-0008: Federation Routing

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee
**Supersedes:** RFC-0005-federation-protocol

## Abstract

Defines how SovereignStack nodes discover each other, negotiate trust, route requests, and replicate data across administrative boundaries while maintaining sovereignty.

## Motivation

A distributed intelligence network requires nodes to cooperate without central coordination. Federation routing provides discovery, trust negotiation, request routing, and data synchronization — all while respecting each node's sovereignty.

## Specification

### Node Advertisement

Nodes advertise their presence and capabilities:

```json
{
  "id": "node://eu-node-001",
  "type": "node",
  "owner": "org://provider",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:00:00Z",
  "signature": "sig:abc...",
  "provenance": [],
  "node": {
    "display_name": "EU Node 001",
    "jurisdiction": "EU",
    "protocols": ["sip/1.0", "sep/0.1", "sap/0.1"],
    "capabilities": ["capability://memory.store", "capability://knowledge.query"],
    "network": {
      "addresses": [
        {"protocol": "wss", "host": "eu-node-001.sovereignstack.io", "port": 8546}
      ],
      "region": "eu-west-1"
    },
    "trust": {
      "trust_score": 85,
      "certification": "L2",
      "certification_valid_until": "2027-05-31"
    },
    "load": {
      "active_sessions": 12,
      "cpu_usage_pct": 34.5,
      "memory_usage_pct": 52.1
    }
  }
}
```

### Discovery Mechanisms

| Mechanism | Scope | Latency | Deterministic |
|-----------|-------|---------|---------------|
| mDNS | Local subnet | ms | Yes |
| DNS SRV | Configured domain | ms | Yes |
| Peer Exchange | Bootstrap list | s | Partial |
| DHT (Kademlia) | Global network | s | No |

### Trust Negotiation

```
Node A                    Node B
  │                         │
  ├── Introduce ──────────► │
  │                         ├── Verify identity
  │                         ├── Check reputation
  │                         ├── Evaluate policy
  │◄── Trust Established ───┤
  │                         │
  ├── Capability Exchange ► │
  │◄── Peer Capabilities ───┤
```

### Routing Table

```json
{
  "peer": "node://us-node-001",
  "status": "connected",
  "trust_score": 82,
  "capabilities": ["capability://reason.legal", "capability://knowledge.query"],
  "latency_ms": 45,
  "last_seen": "2026-05-31T12:00:00Z",
  "routing_cost": 1.2
}
```

### Request Routing

Requests are routed based on:

1. **Capability match** — Does the peer offer the required capability?
2. **Trust score** — Is the peer above minimum threshold?
3. **Jurisdiction** — Does the peer's jurisdiction match policy?
4. **Latency** — Prefer lower latency
5. **Load** — Prefer less loaded peers

### Replication Model

Data replication between federated nodes:

```json
{
  "replication": {
    "source": "node://eu-node-001",
    "target": "node://us-node-001",
    "object_uri": "knowledge://science/physics/newton/v1",
    "policy": "opt-in",
    "sync_mode": "event-driven",
    "last_synced": "2026-05-31T12:00:00Z",
    "merkle_proof": "sha256:abc..."
  }
}
```

Sync modes:
- **event-driven** — Real-time via event bus subscription
- **periodic** — Batch sync at intervals
- **on-request** — Pull on demand

### Federation Policy

```json
{
  "federation": {
    "enabled": true,
    "mode": "peer",
    "trusted_nodes": ["node://trusted-peer-1"],
    "discovery": {
      "dns_domain": "sovereignstack.io",
      "bootstrap": ["node://bootstrap-1", "node://bootstrap-2"],
      "dht_enabled": false
    },
    "routing": {
      "max_hops": 3,
      "timeout_ms": 5000,
      "trust_min": 50
    },
    "replication": {
      "allowed_directions": ["inbound", "outbound"],
      "jurisdiction_filter": ["EU", "US"],
      "max_object_size_mb": 100
    }
  }
}
```

## Security Considerations

- All peer communications are encrypted (TLS/WSS)
- Trust is ephemeral and periodically re-verified
- DHT is opt-in; DNS/bootstrap are preferred
- Replication respects jurisdiction policies
- Malicious peers are blacklisted locally

## Reference Implementation

- `ss-federation` crate: discovery, routing, replication
- Conformance tests: `conformance/tests/sip/`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
