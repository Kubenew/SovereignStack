# RFC-0029: Intelligence Economy Primitives

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0004, RFC-0016

## Summary

Defines the primitive economic primitives for the Sovereign Intelligence Network — resource pricing, compute credits, capability markets, and settlement.

## Specification

### Resource Pricing

| Resource | Unit | Reference Price |
|----------|------|----------------|
| GPU compute | token/s | 0.000001 credits |
| HBM memory | GB·s | 0.0000001 credits |
| Bandwidth | GB | 0.001 credits |
| Storage | GB·day | 0.0001 credits |

### Capability Market

Agents can offer capabilities at a price. Requesters discover via registry and pay for usage:

```json
{
  "offer": {
    "capability": "capability://legal-review/v3",
    "provider": "agent://law-firm-ai",
    "price_per_call": 0.05,
    "min_trust_score": 0.8
  }
}
```

### Settlement

- Off-chain credit accounting for high-frequency micro-transactions
- On-chain settlement for disputes or large transfers
- All settlements recorded in audit log (RFC-0022)

### Core Types

`ResourcePrice`, `CapabilityOffer`, `CreditAccount`, `SettlementRecord`
