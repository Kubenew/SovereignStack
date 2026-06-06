# RFC-0017: Sovereign Memory Protocol (Detailed)

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0006

## Summary

Detailed specification of the Sovereign Memory Protocol (SMP) — the lifecycle, tiering, and query interface for memory objects.

## Specification

### Memory Tiers

| Tier | Backing Store | Latency | Persistence | Max Size |
|------|--------------|---------|-------------|----------|
| L1 Session | Volatile RAM | <10µs | Session lifetime | 1 GB |
| L2 Working | RAM + SSD | <1ms | Days | 64 GB |
| L3 Long-term | SSD + CAS | <10ms | Indefinite | Unlimited |

### Operations

- `store(memory://...)` — create/update
- `recall(memory://...)` — exact retrieval
- `search(query, filters)` — semantic/kNN search across tier
- `archive(memory://...)` — promote to L3 with compaction

### Core Types

`MemoryTier`, `MemoryObject`, `MemoryQuery`, `RecallResult`
