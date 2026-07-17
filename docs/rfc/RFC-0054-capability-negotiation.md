# RFC-0054: Dynamic Capability Negotiation

| Field | Value |
|-------|-------|
| Status | Draft |
| Depends On | RFC-0010, RFC-0048 |
| Module | `ss-swarm/src/negotiation.rs` |

## Overview

Before a task is delegated or a resource is transferred, the two
agents MUST negotiate capabilities. The `Negotiator` struct performs
offer/accept/reject cycles with an optional `SovereignUri` for audit.

## Protocol

1. **Offer** – Initiator sends `CapabilityOffer` with supported actions
2. **Evaluate** – Receiver checks against local policy (RFC-0052)
3. **Accept / Reject / CounterOffer** – Response
4. **Commit** – Both parties record via `policy://` URI

## Implementation

The `Negotiator` in `ss-swarm/src/negotiation.rs` implements this
protocol with timeout and retry logic.
