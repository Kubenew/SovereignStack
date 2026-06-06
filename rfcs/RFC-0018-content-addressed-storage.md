# RFC-0018: Content-Addressable Storage

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0012

## Summary

Defines the content-addressable storage (CAS) layer for immutable, verifiable blob storage addressed by cryptographic hash.

## Specification

### CAS URI

`cas://<hash-algorithm>:<hex-digest>` — e.g., `cas://sha256:a1b2c3...`

### Operations

- `put(blob) → cas://sha256:<digest>` — store and return address
- `get(cas://...) → blob` — retrieve by hash
- `verify(cas://...) → bool` — verify integrity
- `pin(cas://...)` — prevent garbage collection

### Deduplication

CAS automatically deduplicates — identical content produces the same hash. Reference counting tracks pin state.

### Core Types

`CasAddress`, `CasBlob`, `CasStore`, `PinRecord`
