# RFC-0055: Circuit Breaker Policy

| Field | Value |
|-------|-------|
| Status | Draft |
| Depends On | RFC-0050, RFC-0052 |
| Module | `ss-policy/src/circuit_breaker.rs` |

## Overview

When a lease expires or a resource threshold is breached, the
Circuit Breaker terminates the offending container with a recorded
`lease://revocation` entry.

## States

- **Closed** – normal operation
- **Open** – actively terminating, no new requests
- **Half-Open** – testing after cool-down before fully closing

## Implementation

`CircuitBreaker` in `ss-policy/src/circuit_breaker.rs` tracks
lease expiry and resource metrics. On breach, it:
1. Records the event via `safeguard://`
2. Sends SIGTERM to the container
3. Logs outcome via `evidence://`
