# RFC 0004: Federation Protocol Specification

| Field | Value |
|---|---|
| **Status** | Draft |
| **Author** | SovereignStack Core Team |
| **Created** | 2026-05-27 |
| **Category** | Standards Track |

---

## Summary

Define the Sovereign Federation Protocol — the wire protocol and state synchronization mechanism that enables multiple sovereign nodes to form a trust-aware, jurisdictionally-enforced, offline-capable mesh. The protocol handles peer discovery, authenticated connections, CRDT-based state sync, and policy-gated cross-jurisdiction data exchange.

---

## Motivation

Sovereign nodes must operate independently (air-gapped) but periodically synchronize with peers to share non-sensitive metadata, route inference requests across the mesh, and propagate policy updates. No existing protocol satisfies all of:

- **Offline-first**: Nodes must work without connectivity and merge on reconnection
- **Jurisdictional gating**: Data must not cross borders unless policy permits
- **Trust-aware**: Each node must verify peer identity (see RFC 0003)
- **CRDT sync**: Conflict-free replicated data types for vector indices and policy
- **Lightweight**: Suitable for edge/ARM nodes with limited bandwidth

---

## Design

### Protocol Stack

```
┌──────────────────────────────────────────────────────────┐
│                Application Layer                           │
│  Sync (CRDT events)  ·  Discovery (DNS-SD)  ·  Routing   │
├──────────────────────────────────────────────────────────┤
│                Security Layer                              │
│  mTLS (node certs)  ·  WireGuard (transport)             │
├──────────────────────────────────────────────────────────┤
│                Transport Layer                             │
│  QUIC / TCP : 51901  ·  HTTP/2 for discovery             │
└──────────────────────────────────────────────────────────┘
```

### Peer Discovery

| Method | Mechanism | Use Case |
|---|---|---|
| **DNS-SD** | `_sovereign-node._tcp` SRV records | Dynamic mesh |
| **Static config** | YAML peer list | Air-gapped / deterministic |
| **Gossip** | Each node propagates known peers | Large mesh |

### Connection Establishment

```
1. Peer A resolves Peer B via discovery
2. WireGuard handshake (mutual pubkey verification)
3. mTLS handshake over WireGuard (certificate chain validation)
4. Node identity documents exchanged and verified
5. Capability negotiation (sync version, supported CRDT types)
6. Session established
```

### Event Sync Protocol

State is synchronized using an event-sourced model:

```
Peer A                          Peer B
  │                               │
  │───── SYNC_REQUEST ──────────►│  (includes A's state digest)
  │                               │
  │◄──── SYNC_ACK ──────────────│  (includes missing ranges)
  │                               │
  │───── EVENTS ────────────────►│  (batch of new events)
  │  [{event_id, type, data,     │
  │    timestamp, signature}]     │
  │                               │
  │◄──── SYNC_COMPLETE ──────────│  (new state digest)
  │                               │
```

### Event Types

| Event Type | CRDT Type | Purpose |
|---|---|---|
| `memory.vector.upsert` | LWW-Register | Vector index update |
| `memory.vector.delete` | Tombstone Set | Vector index removal |
| `policy.update` | LWW-Register | Policy rule change |
| `node.heartbeat` | LWW-Register | Node availability |
| `audit.log` | Append-Only | Cross-node audit events |

### Message Format

```json
{
  "protocol_version": "1.0",
  "message_type": "SYNC_REQUEST",
  "node_id": "eu-fr1-a7f3b2c1",
  "session_id": "sess-4f8a",
  "state_digest": "sha256:9f8c...",
  "since_sequence": 1042,
  "batch_size": 100,
  "jurisdiction": "EU-GDPR"
}
```

### Jurisdictional Gating

Each event carries a jurisdiction label. Peers enforce policy at the application layer:

```yaml
federation:
  jurisdictions:
    EU-GDPR:
      allowed_egress: ["EU-GDPR"]       # Can only sync with other EU nodes
      denied_types: ["audit.log"]        # Never export audit logs
    US-HIPAA:
      allowed_egress: ["US-HIPAA"]
      denied_types: ["audit.log", "memory.vector.upsert"]
    GLOBAL:
      allowed_egress: ["EU-GDPR", "US-HIPAA", "GLOBAL"]
      denied_types: ["audit.log"]
```

Events that violate jurisdiction policy are dropped with an error response.

### Conflict Resolution

CRDT types used:

| Type | Merge Rule |
|---|---|
| **LWW-Register** | Last-Writer-Wins (timestamp + node_id tiebreaker) |
| **Tombstone Set** | Logical union with tombstones |
| **Append-Only** | Append, never delete |
| **Map** | Recursive merge per key |

---

## Security Considerations

| Threat | Mitigation |
|---|---|
| Eavesdropping | WireGuard encryption (ChaCha20-Poly1305) |
| Replay | Monotonic sequence numbers per node |
| Event forgery | Ed25519 signature on each event |
| Jurisdiction bypass | Signed jurisdiction field, validated by peer |
| DoS | Rate-limited sync requests, capped batch size |

---

## Compatibility

- Backward compatible with existing `file-based sync` (nodes without federation fall back to local-only)
- Protocol version negotiated during handshake (`protocol_version` field)
- CRDT types can be extended without breaking existing sync

---

## Deployment Strategy

| Phase | Scope |
|---|---|
| Phase 1 | Static peer config, WireGuard mesh, event sync (vector index only) |
| Phase 2 | DNS-SD discovery, gossip propagation, jurisdiction gating |
| Phase 3 | Cross-node inference routing, policy sync |
| Phase 4 | Multi-cluster federation with global coordinators |

---

## Migration Path

Standalone nodes opt into federation by:

```yaml
# Add to sovereign-stack.yaml
federation:
  enabled: true
  mode: "leaf"                       # leaf | hub | coordinator
  sync_interval_seconds: 60
  peers:                             # or use DNS-SD discovery
    - id: "hub"
      endpoint: "hub.sovereign.local:51901"
      public_key: "x3w...Y6Q="
```

---

## Alternatives Considered

| Alternative | Reason Not Selected |
|---|---|
| Centralized cloud sync | Violates air-gapped and sovereignty requirements |
| IPFS / libp2p | Too heavy for ARM/edge, no jurisdictional gating |
| Custom REST API per node | No consistency model, no offline support |
| CRDT over WebRTC | WebRTC signaling requires STUN/TURN (WAN dependency) |

---

## References

- [CRDT Paper (Shapiro et al.)](https://hal.science/inria-00555588/)
- [WireGuard Protocol](https://www.wireguard.com/protocol/)
- [DNS-Based Service Discovery (RFC 6763)](https://datatracker.ietf.org/doc/html/rfc6763)
