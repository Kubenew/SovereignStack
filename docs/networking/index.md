# Sovereign Networking & Federation Mesh

The networking layer provides inter-node communication, service discovery, trust propagation, and offline-synchronized federation across sovereign nodes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FEDERATED SOVEREIGN MESH                      │
│                                                                   │
│  ┌──────────┐     WireGuard      ┌──────────┐     WireGuard      ┌──────────┐
│  │  Node A  │◄──────────────────►│  Node B  │◄──────────────────►│  Node C  │
│  │  EU-FR1  │                    │  EU-DE2  │                    │  US-NY3  │
│  └────┬─────┘                    └────┬─────┘                    └────┬─────┘
│       │                               │                               │
│       │         ┌─────────────┐       │                               │
│       │         │  Discovery   │       │                               │
│       └────────►│  (DNS-SD)    │◄──────┘                               │
│                 └──────┬──────┘                                        │
│                        │                                              │
│                 ┌──────▼──────┐                                        │
│                 │  Sync       │◄────────────────────────────────────────┘
│                 │  (CRDT)     │
│                 └─────────────┘
└─────────────────────────────────────────────────────────────────┘
```

### Node Roles

| Role | Description | Example |
|---|---|---|
| **Leaf Node** | Single sovereign node, may sync with upstream | Office, edge device |
| **Regional Hub** | Aggregates multiple leaf nodes, provides upstream federation | Datacenter |
| **Global Coordinator** | Root-level federation, trust anchor, discovery root | Enterprise HQ |

---

## Mesh Topology

### Supported Topologies

| Topology | Use Case | Latency | Complexity |
|---|---|---|---|
| **Star** | Hub-and-spoke, hub provides discovery + sync | Low (hub) | Simple |
| **Full Mesh** | Every node connects to every other | Lowest | High (N²) |
| **Partial Mesh** | Nodes connect to nearest peers, gossip protocol | Medium | Moderate |
| **Hierarchical** | Leaf → Regional → Global | Variable | Moderate |

### Default: Hierarchical hybrid

```
Global Coordinator
├── Regional Hub (EU)
│   ├── Leaf Node (Paris)
│   └── Leaf Node (Berlin)
├── Regional Hub (US)
│   ├── Leaf Node (New York)
│   └── Leaf Node (San Francisco)
└── Regional Hub (APAC)
    └── Leaf Node (Tokyo)
```

---

## Service Discovery

Nodes discover each other via DNS Service Discovery (DNS-SD) with optional static peer configuration.

### Dynamic Discovery (DNS-SD)

```yaml
networking:
  discovery:
    method: "dns-sd"
    domain: "sovereign.local"
    service: "_sovereign-node._tcp"
```

### Static Peer Configuration

```yaml
networking:
  discovery:
    method: "static"
    peers:
      - id: "eu-de2"
        endpoint: "10.0.1.10:51820"
        public_key: "x3w...Y6Q="
      - id: "us-ny3"
        endpoint: "10.0.2.10:51820"
        public_key: "a7f...Z2k="
```

---

## WireGuard Mesh

All inter-node traffic runs over **WireGuard** — an authenticated, encrypted tunnel with minimal overhead.

### Node Identity

Each node has a persistent WireGuard key pair. The public key is the node's identity in the mesh.

```bash
# Generate node key pair
wg genkey | tee /etc/sovereign/node.key | wg pubkey > /etc/sovereign/node.pub

# Peer configuration
[Interface]
PrivateKey = <node-private-key>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
# Regional Hub
PublicKey = <hub-public-key>
Endpoint = hub.sovereign.local:51820
AllowedIPs = 10.0.0.0/8
```

### WireGuard Mesh Configuration

```yaml
networking:
  mesh:
    enabled: true
    protocol: "wireguard"
    port: 51820
    cidr: "10.0.0.0/8"
    mtu: 1420
    peers:
      - id: "hub"
        endpoint: "hub.sovereign.local:51820"
        public_key: "x3w...Y6Q="
        allowed_ips: ["10.0.0.0/8"]
        persistent_keepalive: 25
```

---

## Trust Propagation

Trust flows from the global coordinator downward. Each node must be attested by its upstream peer.

### Trust Chain

```
Global Coordinator (root CA)
  └── Signs Regional Hub CSRs
        └── Signs Leaf Node CSRs
```

| Step | Action | Validation |
|---|---|---|
| 1 | Leaf generates key pair | Local TPM 2.0 |
| 2 | Leaf sends CSR to regional hub | Signed by TPM-attested key |
| 3 | Hub validates leaf identity | Verifies TPM attestation |
| 4 | Hub signs leaf certificate | Returns signed cert |
| 5 | Leaf connects to mesh | WireGuard + mTLS |

---

## Synchronization Protocol

Nodes synchronize state using an **event-sourced CRDT** model:

1. Each node maintains an append-only event log
2. Events are replicated via gossip protocol (every 30s)
3. Conflicts are resolved via Last-Writer-Wins (LWW) per CRDT type
4. Full state is exchanged on reconnection after offline period

### Sync Payload

```json
{
  "node_id": "eu-fr1",
  "sequence": 1042,
  "events": [
    {
      "id": "evt-8192",
      "type": "memory.vector.upsert",
      "timestamp": "2026-05-27T09:00:00Z",
      "data": {"doc_id": "doc-123", "vector_hash": "a1b2..."}
    }
  ],
  "state_digest": "sha256:4f8c..."
}
```

### Offline Operation

| Duration | Behavior | Reconnection |
|---|---|---|
| < 1 hour | Buffer events, periodic retry | Full sync digest |
| 1–24 hours | Buffer events, exponential backoff | Incremental sync |
| > 24 hours | Full state exchange | Full sync + conflict resolution |

---

## Configuration

```yaml
networking:
  mesh:
    enabled: true
    protocol: "wireguard"
    port: 51820
    cidr: "10.0.0.0/8"
  discovery:
    method: "dns-sd"
    domain: "sovereign.local"
  sync:
    protocol: "crdt-gossip"
    interval_seconds: 30
    offline_buffer_hours: 24
  trust:
    provider: "spiffe"
    root_ca: "/etc/sovereign/ca.pem"
    tpm_attestation: true
```

---

## Security

| Concern | Control |
|---|---|
| **Eavesdropping** | WireGuard encryption (ChaCha20-Poly1305) |
| **Node spoofing** | TPM-attested node identity + SPIFFE/SPIRE |
| **Replay attacks** | Event log with monotonic sequence numbers |
| **Sync poisoning** | CRDT validation + state digest verification |
| **Trust compromise** | Short-lived certificates, automatic revocation |

---

## Federation Boundaries

```
Sovereign Mesh
├── Cluster A (EU, GDPR jurisdiction)
│   └── Nodes [eu-fr1, eu-de2, eu-nl3]
├── Cluster B (US, HIPAA jurisdiction)
│   └── Nodes [us-ny3, us-ca4]
└── Cross-Cluster Federation (opt-in, policy-gated)
    └── Only non-PII metadata, aggregated metrics
```

Jurisdictional boundaries are enforced at the mesh router level. Cross-jurisdiction sync is blocked by policy unless explicitly permitted.

---

## See Also

- [Federation Specification](/specs/) (planned)
- [Security Threat Model](/docs/security/threat-model.md)
- [Identity Layer](/docs/architecture/index.md#2-identity--access-flow-oidc--rbac)
