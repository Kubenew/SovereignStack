# RFC-0025: Session Migration

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0003, RFC-0009

## Summary

Defines how active sessions (including KV cache state) are migrated between nodes for load balancing, maintenance, or failure recovery.

## Specification

### Migration Phases

1. **Freeze** — pause session, snapshot KV cache + memory state
2. **Transfer** — move snapshot to target node (RFC-0034 handles KV placement)
3. **Resume** — restore session on target, redirect clients
4. **Cleanup** — release frozen resources on source node

### Session Migration Record

```json
{
  "migration_id": "mig-002",
  "session_id": "session://abc123",
  "source_node": "node://gpu-003",
  "target_node": "node://gpu-015",
  "state_size_mb": 1024,
  "kv_cache_size_mb": 512,
  "downtime_ms": 250,
  "status": "completed"
}
```

### Core Types

`SessionMigration`, `MigrationPlan`, `MigrationExecutor`, `Checkpoint`
