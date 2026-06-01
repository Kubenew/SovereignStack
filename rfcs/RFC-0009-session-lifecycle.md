# RFC-0009: Session Lifecycle

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the session lifecycle — from creation through execution, suspension, resumption, and termination. Sessions are the fundamental execution context for all agent activity in SovereignStack.

## Motivation

Every agent operation occurs within a session. Sessions provide isolation, resource control, capability scoping, and audit boundaries. A standard session model ensures consistent behavior across all implementations.

## Specification

### Session Object

```json
{
  "id": "session://sess-a1b2c3d4",
  "type": "session",
  "owner": "agent://requestor",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:05:00Z",
  "signature": "sig:abc...",
  "provenance": [],
  "session": {
    "status": "running",
    "agent": "agent://worker",
    "parent_session": null,
    "capabilities": [
      "capability://memory.read",
      "capability://knowledge.query",
      "capability://reason.record"
    ],
    "resource_limits": {
      "cpu_time_seconds": 30,
      "memory_mb": 512,
      "wall_clock_seconds": 60,
      "network_calls": 100,
      "child_sessions": 5
    },
    "resource_usage": {
      "cpu_time_seconds": 12.5,
      "memory_mb": 234,
      "wall_clock_seconds": 25.3,
      "network_calls": 42,
      "child_sessions": 2
    },
    "ttl": "2026-05-31T13:00:00Z",
    "jurisdiction": "EU",
    "trace_id": "trace-xyz-789"
  }
}
```

### Lifecycle State Machine

```
                    ┌──────────────┐
                    │   PENDING    │
                    └──────┬───────┘
                           │ allocate
                           ▼
                    ┌──────────────┐
              ┌────►│   RUNNING    │◄────┐
              │     └──────┬───────┘     │
              │            │             │
         suspend        complete      resume
              │            │             │
              │     ┌──────┴───────┐     │
              └─────┤   SUSPENDED  ├─────┘
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │  TERMINATED  │
                    └──────────────┘

  PENDING     → Resources allocated, agent not yet active
  RUNNING     → Agent executing
  SUSPENDED   → Execution paused, resources held
  TERMINATED  → Resources released, audit finalized
  FAILED      → Abnormal termination
```

### State Transitions

| From | To | Trigger | Validators |
|------|----|---------|------------|
| PENDING | RUNNING | Resource allocation confirmed | Resource limits, capabilities |
| RUNNING | SUSPENDED | Timeout, policy, manual pause | Authorization |
| SUSPENDED | RUNNING | Resume request | TTL check, resource availability |
| RUNNING | TERMINATED | Successful completion | None |
| RUNNING | FAILED | Error, exception | None |
| SUSPENDED | TERMINATED | TTL expiry, manual termination | Authorization |
| Any | TERMINATED | Force-terminate (admin) | Admin capability |

### Session Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Create | `POST /sessions` | Open a new session |
| Get | `GET /sessions/{id}` | Retrieve session state |
| Suspend | `POST /sessions/{id}/suspend` | Pause execution |
| Resume | `POST /sessions/{id}/resume` | Resume execution |
| Terminate | `DELETE /sessions/{id}` | End session |
| List | `GET /sessions` | List active sessions |

### Resource Enforcement

```
Request ──► Resource Monitor ──► Limit Check ──► Allow/Deny
                │                      │
                ▼                      ▼
          Usage Counter           Policy Engine
```

When a limit is reached:
- **soft limit**: Warning emitted, session continues
- **hard limit**: Session suspended or terminated

### Capability Scoping

Capabilities are scoped to session lifetime:

- Session created → capabilities derived from agent + parent session
- Session running → capabilities active
- Session terminated → all derived capabilities revoked

### Audit Trail

Every session state transition generates an event (RFC-0007):

```
session.created  → event://session.created
session.running  → event://session.started
session.paused   → event://session.suspended
session.stopped  → event://session.terminated
session.failed   → event://session.failed
```

## Security Considerations

- Sessions are isolated from each other
- Capabilities are scoped to session lifetime
- Resource limits prevent DoS
- Force-terminate requires admin capability
- Audit trail is immutable and signed

## Reference Implementation

- `ss-sessiond` crate: session daemon
- `ss-kernel::capability` — capability scoping
- Conformance tests: `conformance/tests/sap/`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
