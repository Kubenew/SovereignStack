# Federation Protocol

The Federation Protocol enables sovereign nodes to form a trust-aware, jurisdictionally-enforced, offline-capable mesh for cross-node synchronization and inference routing.

This document provides an overview of federation concepts. For the wire protocol specification, see [RFC 0004](/rfcs/0004-federation-protocol.md).

---

## Federation Topologies

| Topology | Description | Best For |
|---|---|---|
| **Standalone** | Single node, no federation | Personal, Air-Gapped |
| **Hub & Spoke** | One coordinator node, many leaf nodes | Enterprise branch offices |
| **Full Mesh** | Every node peer-to-peer | Small trusted networks |
| **Hierarchical** | Leaf → Regional Hub → Global Coordinator | Multi-region, multi-jurisdiction |

---

## What Gets Synchronized

| Data | Sync Direction | CRDT Type |
|---|---|---|
| Vector index (metadata only) | Bidirectional | LWW-Register |
| Policy rules | Hub → Leaves | LWW-Register |
| Node heartbeats | Bidirectional | LWW-Register |
| Audit logs (cross-node) | Leaves → Hub | Append-Only |
| Model manifests | Hub → Leaves | LWW-Register |

Vector embeddings themselves are **not** synchronized — only metadata, document IDs, and vector hashes are exchanged. Full vector data stays local.

---

## Jurisdictional Gating

Federation respects data residency. Nodes tag events with a jurisdiction label, and peers enforce egress policies:

```
EU Node (GDPR)  ←──→  EU Node (GDPR)   ✅ Allowed
EU Node (GDPR)  ←──→  US Node (HIPAA)   ❌ Blocked (default)
EU Node (GDPR)  ←──→  Global Coordinator 🟡 Metadata only (no audit logs, no vectors)
```

Jurisdiction is encoded in the node certificate (see [RFC 0003](/rfcs/0003-node-identity.md)) and enforced at the protocol layer.

---

## Offline Operation

Nodes are designed for **offline-first** operation:

| Scenario | Behavior |
|---|---|
| Network available | Sync events every N seconds (configurable) |
| Network lost | Buffer events locally, retry with exponential backoff |
| Reconnection | Full state digest exchange, then incremental sync |
| >24h offline | Full state exchange (all events since last sync) |

---

## Configuration

```yaml
federation:
  enabled: true
  mode: "leaf"                     # leaf | hub | coordinator
  sync_interval_seconds: 60
  batch_size: 100
  discovery:
    method: "dns-sd"               # dns-sd | static
    domain: "sovereign.local"
  jurisdiction:
    region: "EU"
    policy: "GDPR"
  peers:
    - id: "hub"
      endpoint: "hub.sovereign.local:51901"
      public_key: "x3w...Y6Q="
```

---

## CLI Commands

```bash
# Show federation status
sovereign federation status

# List connected peers
sovereign federation peers

# Force manual sync
sovereign federation sync

# Show pending events
sovereign federation pending

# Check jurisdiction policy
sovereign federation jurisdiction --region EU --policy GDPR
```

---

## See Also

- [RFC 0003: Node Identity](/rfcs/0003-node-identity.md)
- [RFC 0004: Federation Protocol](/rfcs/0004-federation-protocol.md)
- [Networking Mesh](/docs/networking/index.md)
- [Deployment Profiles](/docs/deployment/profiles.md)
