# SovereignStack Economy (`ss-economy`)

The `ss-economy` crate provides the financial and economic primitives for the Sovereign Intelligence Network. It maps directly onto real financial institution domains, enabling digital twins (`person://`, `company://`, `bank://`) and sovereign agents to participate in programmable economies.

## Feature Flags

The crate is decomposed into 12 feature-gated modules. All features are enabled by default.

| Module | Feature | Domain |
|--------|---------|--------|
| `payments` | `payments` | Payment processing & transfers (DvP, PvP) |
| `settlement` | `settlement` | Trade & payment settlement engine |
| `treasury` | `treasury` | Treasury, cash positioning & liquidity management |
| `assets` | `assets` | Tokenized real-world asset (RWA) registry |
| `markets` | `markets` | Order books, trading matching, and market data |
| `insurance` | `insurance` | Policies, coverage, claims, and underwriting |
| `risk` | `risk` | Risk models, Value at Risk (VaR), and stress testing |
| `derivatives` | `derivatives` | Options (with Greeks), futures, swaps, forwards |
| `accounting` | `accounting` | Double-entry ledger, journal entries, trial balances |
| `tax` | `tax` | Tax computation, jurisdiction rules, treaty benefits |
| `fin_identity` | `fin_identity` | KYC verification, AML checks, and sanctions screening |
| `fin_compliance` | `fin_compliance` | Regulatory compliance engine (ISO 20022, PSD2, Basel III) |

## Usage

Add to your `Cargo.toml`:

```toml
[dependencies]
ss-economy = { version = "0.1.0", features = ["payments", "assets", "accounting"] }
```

## Integration with RFC-0060

This crate implements the data models and traits for the "Economic State" layer of Digital Twin Objects defined in [RFC-0060](../rfcs/RFC-0060-digital-twin-entity-model.md).

It utilizes the Financial Economy URI schemes:
- `payment://<id>`
- `settlement://<id>`
- `treasury://<id>`
- `derivative://<id>`
- `insurance://<id>`
- `account://<ledger>/<id>`
- `tax://<jurisdiction>/<id>`
