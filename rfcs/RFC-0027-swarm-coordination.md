# RFC-0027: Swarm Coordination

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0007, RFC-0014

## Summary

Defines how multiple agents coordinate as a swarm — leader election, task distribution, result aggregation, and failure recovery.

## Specification

### Swarm Topology

```
Leader ← Worker 1, Worker 2, ..., Worker N
         ↓
    Observer (backup leader)
```

### Coordination Messages

| Message | From | Purpose |
|---------|------|---------|
| `heartbeat` | Worker → Leader | Liveness + load report |
| `task_offer` | Leader → Worker | Propose task execution |
| `task_accept` | Worker → Leader | Accept + lock resources |
| `task_result` | Worker → Leader | Return result + provenance |
| `rebalance` | Leader → All | Redistribute work |
| `leader_elect` | All | RAFT-based election |

### Core Types

`SwarmTopology`, `SwarmMember`, `TaskOffer`, `TaskResult`, `ElectionState`
