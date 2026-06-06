# RFC-0020: Policy Enforcement

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001

## Summary

Defines how governance policies are authored, distributed, evaluated, and enforced across the SovereignStack runtime.

## Specification

### Policy Document

```json
{
  "id": "policy://gdpr-eu/v2",
  "jurisdiction": "EU",
  "rules": [
    {"effect": "deny", "action": "transfer", "resource": "personal_data", "target_jurisdiction": "non-eu"},
    {"effect": "allow", "action": "infer", "resource": "anonymized_data", "condition": "anonymization_level >= 0.95"}
  ],
  "priority": 100,
  "valid_from": "2026-01-01T00:00:00Z",
  "valid_until": "2027-01-01T00:00:00Z"
}
```

### Evaluation Engine

Policies are evaluated in priority order. First matching rule determines allow/deny. Evaluation result includes matched rule ID and reason.

### Core Types

`Policy`, `PolicyRule`, `PolicyEngine`, `EvaluationResult`
