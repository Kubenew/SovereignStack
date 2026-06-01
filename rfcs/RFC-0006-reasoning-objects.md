# RFC-0006: Reasoning Objects

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines Reasoning Objects — immutable, verifiable traces of inference, deduction, and decision-making. Every reasoning step is recorded as a first-class object that can be replayed, audited, and shared.

## Motivation

In current AI systems, reasoning is ephemeral. The chain-of-thought that produced a result is lost after inference. SovereignStack makes reasoning a first-class object — enabling audit, replay, sharing, and verification of how any conclusion was reached.

## Specification

### Reasoning Object

```json
{
  "id": "reason://legal/gdpr/analysis-17",
  "type": "reason",
  "owner": "agent://legal-analyst",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:00:00Z",
  "signature": "sig:abc...",
  "provenance": [],
  "reasoning": {
    "trigger": "capability://legal-review invoked on artifact://doc-001",
    "goal": "Determine GDPR compliance of data processing clause",
    "status": "completed",
    "steps": [
      {
        "id": "step-001",
        "type": "retrieval",
        "input": "Extract processing purposes from clause 3.1",
        "output": "knowledge://doc-001/clause-3.1",
        "confidence": 0.98,
        "started_at": "2026-05-31T12:00:00Z",
        "completed_at": "2026-05-31T12:00:02Z",
        "dependencies": []
      },
      {
        "id": "step-002",
        "type": "query",
        "input": "Query GDPR requirements for processing purposes",
        "output": "knowledge://gdpr/article5/v2",
        "confidence": 0.99,
        "started_at": "2026-05-31T12:00:03Z",
        "completed_at": "2026-05-31T12:00:05Z",
        "dependencies": []
      },
      {
        "id": "step-003",
        "type": "deduction",
        "input": "Compare processing purposes against GDPR article 5",
        "output": "knowledge://gdpr-compliance/assessment-17",
        "confidence": 0.92,
        "started_at": "2026-05-31T12:00:06Z",
        "completed_at": "2026-05-31T12:00:30Z",
        "dependencies": ["step-001", "step-002"],
        "rationale": "Article 5 requires explicit consent for each processing purpose. Clause 3.1 lists purposes but no consent mechanism. Non-compliant."
      }
    ],
    "result": {
      "conclusion": "non-compliant",
      "confidence": 0.92,
      "output": "knowledge://gdpr-compliance/assessment-17",
      "summary": "Clause 3.1 fails GDPR Article 5: no consent mechanism"
    },
    "metrics": {
      "total_duration_ms": 30000,
      "steps_completed": 3,
      "steps_failed": 0,
      "tokens_used": 4500
    }
  }
}
```

### Step Types

| Type | Description | Verifiable |
|------|-------------|------------|
| `retrieval` | Fetch knowledge or memory | Yes (content hash) |
| `query` | Query a capability or database | Yes (response signature) |
| `deduction` | Logical inference from premises | Yes (formal proof) |
| `induction` | Generalize from examples | Partial |
| `abduction` | Infer explanation for observation | Partial |
| `computation` | Numerical/algorithmic operation | Yes (reproducible) |
| `decision` | Branch based on condition | Yes (condition trace) |
| `delegation` | Sub-task assigned to another agent | Yes (binding ref) |

### Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Create | `POST /reasons` | Record a reasoning trace |
| Read | `GET /reasons/{id}` | Retrieve by ID |
| Replay | `POST /reasons/{id}/replay` | Re-execute reasoning steps |
| Compare | `POST /reasons/compare` | Diff two reasoning traces |
| Query | `POST /reasons/query` | Search by goal, conclusion, agent |

### Replay

A reasoning object **must** contain sufficient information to be replayed:

```json
{
  "replay": {
    "reproducible": true,
    "deterministic_steps": ["step-001", "step-003"],
    "non_deterministic_steps": ["step-002"],
    "expected_output_hash": "sha256:abc123..."
  }
}
```

### Reasoning Graph

Multiple reasoning objects can form a graph:

```
reason://case-001 ──► reason://finding-a
     │                    │
     │                    ▼
     └──► reason://finding-b ──► reason://conclusion
```

## Security Considerations

- Reasoning objects are immutable after creation
- Confidence scores are self-reported; trust model (RFC-0003) validates the agent
- Replay verification detects tampering
- Delegation steps reference capability bindings (RFC-0004)

## Reference Implementation

- `ss-reason` crate: reasoning trace storage, replay engine
- Protocol: REP (Reasoning Exchange Protocol)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
