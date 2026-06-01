# 07 — Governance & Policy

**Layer:** Infrastructure → Application
**Status:** Draft
**Source:** `ss-policy/`

## Overview

Governance defines the rules by which the system operates. Policies are expressed as machine-readable objects that the kernel's Policy Engine evaluates on every operation.

## Policy Object

```json
{
  "uri": "policy://gdpr-data-residency",
  "type": "policy",
  "version": "1.0.0",
  "jurisdiction": "EU",
  "rules": [
    {
      "effect": "deny",
      "action": "egress",
      "resource": "personal_data",
      "condition": "destination_jurisdiction != 'EU'"
    }
  ],
  "enforcement": "hard",  // hard | soft | audit-only
  "signature": "sig:abc..."
}
```

## Policy Types

| Policy | Scope | Enforcement |
|--------|-------|-------------|
| Data Residency | Jurisdiction | Hard |
| Access Control | Resource | Hard |
| Retention | Data type | Hard |
| Federation | Network | Configurable |
| Audit | All | Always-on |
| Resource Limits | Session | Hard |

## Governance Hierarchy

```
Constitution (immutable)
  └── Governance Policy (node-level)
       └── Organizational Policies
            └── Agent-level Policies
                 └── Session-level Overrides
```

## Human Override

Any policy can be overridden by a human administrator with appropriate authority. Overrides are:
- Logged to immutable audit trail
- Time-bound (default 24h)
- Require multi-party approval for sensitive operations
