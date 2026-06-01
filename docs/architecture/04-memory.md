# 04 — Memory Hierarchy

**Layer:** Intelligence
**Status:** Draft
**Source:** `ss-memory/`

## Overview

SovereignStack defines a tiered memory hierarchy from ephemeral session state to civilizational knowledge.

## Memory Tiers

```
Tier 0: Session Memory    (seconds–minutes)     Volatile, in-process
     │
     ▼
Tier 1: Personal Memory   (days–weeks)          Persisted, per-agent
     │
     ▼
Tier 2: Org Memory        (months–years)        Shared, organizational
     │
     ▼
Tier 3: Global Memory     (decades)             Civilizational knowledge
```

## Tier Characteristics

| Tier | Storage | Replication | Access | TTL |
|------|---------|-------------|--------|-----|
| 0 | In-memory HashMap | None | Local only | Session lifetime |
| 1 | RocksDB/SQLite | Node-local | Owner + delegates | Days–weeks |
| 2 | Distributed DB | Within org | Org members | Months |
| 3 | CAS + IPFS | Global | Read by capability | Indefinite |

## Memory Operations (SMP)

- `PUT /memory` — Store (with TTL)
- `GET /memory/<uri>` — Retrieve
- `POST /memory/search` — Search by pattern/tags
- `DELETE /memory/<uri>` — Soft delete (tombstone)
- `POST /memory/promote` — Promote to higher tier
