# SFIN — Sovereign Financial Intelligence Network Profile

**Version:** 1.0
**Status:** Draft
**Depends on:** RFC-0073 (Digital Economy Objects), RFC-0074 (Digital Twin Objects)

## Overview

SFIN defines the standards, object models, policies, and conformance requirements for deploying SovereignStack in financial services. It reuses the kernel, governance, and trust layers while adding domain-specific objects, compliance requirements, and integration standards for payments, treasury, settlement, insurance, and regulatory reporting.

## Object Model Extensions

### Required URI Schemes

| URI | Role in SFIN | Required Fields |
|-----|-------------|-----------------|
| `payment://` | ISO 20022 payment instructions | type, sender, receiver, amount, compliance_ref |
| `settlement://` | DVP/FOP settlement records | payment_ref, method, asset, status |
| `treasury://` | Treasury account operations | account, action, amount, approved_by |
| `account://` | General ledger accounts | entity, ledger, balance, currency |
| `insurance://` | Insurance policies | type, coverage, premium, status |
| `tax://` | Taxable events | jurisdiction, type, amount, period |
| `derivative://` | Derivative contracts | type, underlying, strike, expiry |
| `market://` | Financial markets | venue, asset_class, trading_hours |
| `exchange://` | Exchange venues | venue, pairs, order_types |
| `risk://` | Risk models | scope, var_95, stress_scenarios |
| `economy://` | Economic system | jurisdiction, currency, consensus |

### Required Digital Twin Schemes

| URI | Role in SFIN |
|-----|-------------|
| `person://` | KYC-verified individuals |
| `company://` | Corporate entities |
| `bank://` | Financial institutions |
| `portfolio://` | Investment portfolios |
| `fund://` | Investment funds |
| `bond://` | Debt instruments |
| `stock://` | Equity securities |

## Compliance Requirements

### AML/KYC

Every `payment://` object MUST reference a `policy://` compliance check:

```
payment://cbdc/pacs008-001
    └── compliance_ref: policy://aml/kyc-verified
```

### Settlement Finality

All `settlement://` objects MUST reference both the payment and the asset delivery:

```
settlement://dvp/trade-88
    ├── payment_ref: payment://cbdc/pacs008-001
    └── asset: asset://cbdc/eur-001
```

### Audit Trail

Every financial transaction MUST produce a chain of:
1. `payment://` or `derivative://` (instruction)
2. `treasury://` (accounting)
3. `policy://` (compliance)
4. `settlement://` (finality)
5. `evidence://` (audit record)
6. `chain://` (provenance)

### Regulatory Reporting

`tax://` objects MUST be generated for every taxable event and linked to the originating transaction chain.

## Integration Standards

| Standard | Integration Point |
|----------|-------------------|
| ISO 20022 | `payment://` message types (pacs.008, pacs.002, etc.) |
| SWIFT | `payment://swift/` namespace |
| MiFID II | `market://` and `exchange://` compliance |
| GDPR | `person://` consent and privacy |
| Basel III | `risk://` and `treasury://` capital requirements |
| Solvency II | `insurance://` capital requirements |

## Workflow Example

```
1. Person initiates payment
   person://alice → payment://swift/pacs008-001

2. AI Treasury evaluates
   treasury://acme/main-usd/instruction-001

3. Policy engine validates
   policy://engine/aml-v3/evaluation-001

4. DVP settlement
   settlement://dvp/trade-88421

5. Audit record created
   evidence://audit/tx-abc123

6. Provenance chain updated
   chain://sfin/tx-abc123/provenance

7. Tax event generated (if applicable)
   tax://de/vat/evt-20260723
```

## Conformance Levels

| Level | Name | Requirements |
|-------|------|-------------|
| SFIN-L1 | Basic Payments | `payment://`, `account://`, `evidence://` |
| SFIN-L2 | Treasury | + `treasury://`, `settlement://`, `policy://` |
| SFIN-L3 | Markets | + `market://`, `exchange://`, `derivative://`, `risk://` |
| SFIN-L4 | Full Economy | + `insurance://`, `tax://`, `portfolio://`, `fund://` |

## Reference Implementation

See `examples/finance-reference-node/` for a working SFIN-L2 implementation.
