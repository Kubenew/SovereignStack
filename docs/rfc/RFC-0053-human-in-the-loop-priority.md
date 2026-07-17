# RFC-0053: Human-in-the-Loop Priority Injection

| Field | Value |
|-------|-------|
| Status | Draft |
| Depends On | RFC-0052, RFD on Operator override |
| Helm Config | `configmap-human.yaml` |

## Overview

Human operators may inject priority overrides or veto decisions into
the agent mesh. This is formalized as a ConfigMap mounted into the
swarm, consumed by `ss-policy/src/proof_verifier.rs`.

## ConfigMap Schema

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: human-priority-override
data:
  overrides.json: |
    {
      "veto": ["decision-abc-123", "decision-def-456"],
      "priority_routes": {
        "agent-finance": "HIGH",
        "agent-kyc": "LOW"
      },
      "operator_sessions": ["operator://alice", "operator://bob"]
    }
```

## Consumption

The `ProofVerifier` loads overrides on startup and checks them
before accepting or rejecting safety proofs. If an override matches,
the human decision takes precedence.
