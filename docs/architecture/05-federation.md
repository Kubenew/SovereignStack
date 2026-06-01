# 05 — Federation Model

**Layer:** Infrastructure
**Status:** Draft
**Source:** `ss-federation/`

## Overview

SovereignStack nodes form a **sovereign federation** — each node controls its own data, policies, and trust. Federation is always opt-in.

## Discovery

```
mDNS (local subnet)
  │
  ▼
DNS SRV (configured domain)
  │
  ▼
Peer Exchange (bootstrap list)
  │
  ▼
DHT (Kademlia-based)
```

## Trust Establishment

1. Node A discovers Node B
2. Node A requests Node B's identity certificate
3. Node A verifies Node B's certificate chain
4. Optional: mutual capability exchange
5. Trust established for configurable duration

## Federation Policy Example

```json
{
  "federation_enabled": true,
  "trusted_nodes": ["node://peer-1", "node://peer-2"],
  "max_delegation_depth": 3,
  "allowed_operations": ["resolve", "query", "subscribe"],
  "jurisdiction_filter": ["US", "EU", "JP"],
  "replication_policy": "opt-in"
}
```

## Data Sovereignty

- Data never leaves jurisdiction without explicit policy
- Replication respects jurisdiction boundaries
- Each node controls its own data retention
- Cross-border queries go through policy evaluation
