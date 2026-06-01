# 08 — Trust Graph

**Layer:** Infrastructure
**Status:** Draft
**Source:** `ss-trust/`

## Overview

Trust in SovereignStack is not boolean. It is a multi-dimensional graph of identity, verification, certification, and reputation — all expressed as machine-readable objects.

## Trust Objects

| Object | Schema | Source |
|--------|--------|--------|
| Identity | `agent://`, `node://` | Self-issued |
| Verification | `verification://` | Third-party |
| Certification | `certification://` | OASA program |
| Reputation | `reputation://` | Network consensus |
| Trust | `trust://` | Computed |

## Trust Graph

```
Identity ──── has ────► Verification
   │                      │
   │                      ▼
   ├── has ──────────► Certification
   │
   └── has ──────────► Reputation ◄─── Consensus
                           │
                           ▼
                       Trust Score
```

## Trust Document Example

```json
{
  "identity": "agent://research-1",
  "verified": true,
  "verifications": [
    {
      "verifier": "node://certifier",
      "method": "keybase",
      "timestamp": "2026-05-31T00:00:00Z",
      "expires": "2027-05-31T00:00:00Z"
    }
  ],
  "certifications": [
    {
      "level": "L2",
      "issued_by": "OASA",
      "valid_until": "2027-05-31T00:00:00Z"
    }
  ],
  "trust_score": 91,
  "reputation": {
    "total_interactions": 1500,
    "success_rate": 0.98,
    "avg_latency_ms": 42,
    "last_updated": "2026-05-31T00:00:00Z"
  }
}
```

## Trust Usage

- **Routing** — Prefer higher-trust agents for task delegation
- **Federation** — Control which peers can replicate data
- **Capabilities** — Weight trust in delegation decisions
- **Governance** — Enforce minimum trust thresholds
