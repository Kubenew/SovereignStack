# RFC-0021: Jurisdiction & Data Residency

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0020

## Summary

Defines jurisdiction-aware data residency enforcement — ensuring data stays within sovereign boundaries unless explicitly authorized.

## Specification

### Jurisdiction Tag

Every object carries a `jurisdiction` metadata field (ISO 3166-1 alpha-2 code or `GLOBAL`). Nodes enforce that objects cannot cross jurisdiction boundaries without an explicit policy override.

### Data Transfer Rules

| Source | Target | Default | With Override |
|--------|--------|---------|---------------|
| EU | Non-EU | Deny | Allow with audit |
| US | EU | Allow | — |
| CN | Any | Deny | Allow with encryption |
| Any | Same | Allow | — |

### Enforcement Points

1. **Ingress** — API gateway checks source jurisdiction
2. **Federation** — cross-fabric routes are checked against policies
3. **Storage** — CAS replication respects jurisdiction boundaries

### Core Types

`JurisdictionTag`, `DataResidencyPolicy`, `TransferRequest`, `TransferVerdict`
