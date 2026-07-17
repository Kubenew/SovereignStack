# RFC-0052: Safe Resource Fencing

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `sandbox://`, `safeguard://`, `operator://` |
| Depends On | RFC-0010, RFC-0050 |

## Overview

Isolate untrusted agent execution via `sandbox://`, enforce safety
via `safeguard://`, and allow human override via `operator://`.

## URI Schemes

- `sandbox://<zone>/<agent>` – sandboxed execution environment
- `safeguard://<guardian-node>` – safety guard for kill-switch
- `operator://<human>` – human operator identity

## Fencing Flow

1. Suspicious agent placed in `sandbox://`
2. `safeguard://` monitors resource usage
3. If threshold exceeded, circuit breaker (RFC-0050) triggers
4. Human may intervene via `operator://`
