# RFC-0073: Digital Economy Objects

**Status:** Draft
**URI Schemes:** `economy://`, `asset://`, `payment://`, `treasury://`, `market://`, `risk://`, `insurance://`, `settlement://`, `exchange://`, `tax://`, `derivative://`, `account://`
**Depends on:** RFC-0001 (Sovereign Object Model), RFC-0029 (Intelligence Economy)
**Related:** RFC-0074 (Digital Twin Objects), ss-economy/

## Abstract

This RFC defines the digital economy object model for SovereignStack — the native representation of financial instruments, payments, markets, settlements, and economic state as first-class addressable objects with full provenance, governance, and compliance.

## Motivation

Autonomous agents and digital twins need to operate within programmable economies. Today, financial systems are built as siloed APIs with no common object model. SovereignStack treats economic objects as native citizens of the operating system, enabling agents to reason about, transact, and audit economic activity using the same protocol primitives as reasoning and memory.

## Object Definitions

### `economy://` — Digital Economy

Represents a sovereign economic system (e.g., a CBDC network, a tokenized market).

```json
{
  "id": "economy://eu/digital-euro",
  "jurisdiction": "EU",
  "currency": "EUR",
  "consensus": "pbft",
  "participants": ["bank://ecb", "bank://deutsche-bank"],
  "status": "active",
  "governance": "governance://eu/digital-euro-charter"
}
```

### `asset://` — Tokenized Asset

A real-world or digital asset represented on-chain.

```json
{
  "id": "asset://tokenized/berlin-01",
  "type": "real-estate",
  "owner": "company://acme-corp",
  "jurisdiction": "DE",
  "valuation": { "amount": 2500000, "currency": "EUR" },
  "provenance": "chain://berlin-01/history",
  "compliance": "insurance://policy/property-berlin"
}
```

### `payment://` — Payment Instruction

A payment order following ISO 20022 messaging standards.

```json
{
  "id": "payment://swift/pacs008-001",
  "type": "pacs.008",
  "sender": "account://acme/main-usd",
  "receiver": "account://vendor/eur-001",
  "amount": { "value": 50000, "currency": "USD" },
  "status": "pending",
  "compliance_check": "policy://aml/kyb-check",
  "evidence": "evidence://payment-001"
}
```

### `settlement://` — Settlement Record

Final settlement of a trade or payment.

```json
{
  "id": "settlement://dvp/trade-88421",
  "trade": "trade://equity/AAPL/001",
  "payment": "payment://swift/pacs008-001",
  "asset_delivery": "asset://tokenized/aapl-001",
  "status": "settled",
  "timestamp": "2026-07-18T14:30:00Z",
  "provenance": "chain://settlement-88421"
}
```

### Other Economy Objects

| URI | Description | Key Fields |
|-----|-------------|------------|
| `treasury://` | Treasury account | balance, currency, jurisdiction |
| `market://` | Financial market | venue, asset_class, open_hours |
| `risk://` | Risk model | scope, var_95, stress_scenarios |
| `insurance://` | Insurance policy | type, coverage, premium, status |
| `exchange://` | Exchange venue | venue, pairs, order_types |
| `tax://` | Taxable event | jurisdiction, type, amount, period |
| `derivative://` | Derivative contract | type, underlying, strike, expiry |
| `account://` | Ledger account | entity, ledger, balance, currency |

## Security Considerations

- **Atomic Settlement:** Settlement objects MUST reference both payment and asset delivery. Partial settlement is not permitted.
- **Compliance:** Every payment MUST reference a compliance check policy. The policy engine MUST verify before execution.
- **Provenance:** All economic state changes MUST be recorded in the provenance graph.
- **Cross-border:** Multi-jurisdiction transactions MUST declare all applicable jurisdictions.

## Conformance

1. Support all 12 URI schemes with described semantics.
2. Reference compliance policies for all payment/settlement objects.
3. Record all economic state transitions in the provenance graph.
4. ISO 20022 message types supported for payment objects.

## References

- RFC-0001: Sovereign Object Model
- RFC-0029: Intelligence Economy
- RFC-0074: Digital Twin Objects
- ISO 20022 Financial Messaging
