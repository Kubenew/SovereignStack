# RFC-0015: Workflow Execution Engine

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0003

## Summary

Defines the workflow execution model — how composable sequences of agent actions are defined, scheduled, executed, and audited.

## Specification

### Workflow Definition

```json
{
  "id": "workflow://contract-analysis/v2",
  "steps": [
    {"id": "step-1", "action": "ingest", "input": "artifact://contract.pdf"},
    {"id": "step-2", "action": "reason", "input": {"prompt": "Analyze clauses...", "model": "qwen2.5-72b"}},
    {"id": "step-3", "action": "notify", "input": {"target": "agent://legal-review", "result": "step-2.output"}}
  ],
  "error_handler": {"on_failure": "rollback", "max_retries": 3}
}
```

### State Machine

`Pending → Running → Paused → Running → Completed | Failed | RolledBack`

### Core Types

`WorkflowDefinition`, `WorkflowStep`, `WorkflowInstance`, `StepResult`
