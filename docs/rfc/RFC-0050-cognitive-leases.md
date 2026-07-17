# RFC-0050: Cognitive Leases

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `lease://` |
| Depends On | RFC-0010 |

## Overview

Ephemeral agents acquire a `lease://` URI when granted compute or
memory resources. Leases have a TTL and must be periodically renewed.

## URI Scheme

`lease://<agent>/<resource>`

Examples:
- `lease://agent-finance/gpu-003`
- `lease://kyc-verifier/memory-pool-7`

## Lifecycle

1. Agent requests resource; LeaseManager issues `lease://`
2. Agent uses resource; periodic `renew` extends TTL
3. On expiry, LeaseManager collects and may kill container
4. Agent may voluntarily `revoke` the lease

## Implementation

See `scripts/test_cognitive_leases.py` for reference and
`CircuitBreaker` in `ss-policy/src/circuit_breaker.rs` for
safe container termination.
