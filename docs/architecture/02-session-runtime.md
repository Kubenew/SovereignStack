# 02 — Session Runtime

**Layer:** Kernel → Infrastructure
**Status:** Draft
**Source:** `ss-sessiond/`

## Overview

Sessions are ephemeral, sandboxed execution contexts for agents. Every agent operation occurs within a session.

## Session Lifecycle

```
 ┌─────────┐
 │ Created │
 └────┬────┘
      ▼
 ┌────────────┐
 │ Initialized│
 └────┬───────┘
      ▼
 ┌─────────┐      ┌─────────┐
 │ Running │◄────►│ Paused  │
 └────┬────┘      └─────────┘
      │
      ├────────────┐
      ▼            ▼
 ┌──────────┐ ┌─────────┐
 │Completed │ │ Failed  │
 └──────────┘ └─────────┘
```

## Resource Limits

| Resource | Default | Max | Enforced By |
|----------|---------|-----|-------------|
| CPU Time | 30s | 300s | cgroups/rlimit |
| Memory | 512 MB | 4 GB | cgroups |
| Wall Clock | 60s | 600s | Session daemon |
| Network Calls | 100 | 1000 | Proxy |
| Child Sessions | 5 | 50 | Session daemon |

## Isolation

- Each session has a unique cryptographic context
- Capabilities are scoped to session lifetime
- Session termination revokes all derived capabilities
- I/O is logged to audit trail

## Implementation

```rust
pub struct Session {
    id: SessionId,
    agent: AgentUri,
    status: SessionStatus,
    created_at: Timestamp,
    ttl: Duration,
    capabilities: Vec<CapabilityUri>,
    resource_limits: ResourceLimits,
}
```
