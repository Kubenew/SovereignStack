# 06 — Capability System

**Layer:** Kernel
**Status:** Draft
**Source:** `ss-capability/`

## Overview

SovereignStack uses **capability-based security**. Every operation requires an explicit, revocable, auditable capability. There is no implicit trust.

## Capability Structure

```json
{
  "uri": "capability://delegated:read:memory://xyz",
  "type": "capability",
  "granted_by": "node://issuer",
  "granted_to": "agent://recipient",
  "permissions": ["read", "list"],
  "target": "memory://xyz",
  "conditions": {
    "max_uses": 10,
    "expires_at": "2026-06-30T23:59:59Z"
  },
  "signature": "sig:abc..."
}
```

## Capability Types

| Type | Description | Max Depth |
|------|-------------|-----------|
| Direct | Granted by resource owner | N/A |
| Delegated | Transferred from holder | 3 levels |
| Derived | Auto-granted from parent session | Session scope |

## Enforcement Flow

```
Request → Extract capability → Verify signature
  → Check expiration → Check revocation → Check conditions
  → Grant or Deny
```

## Revocation

- Direct revocation via CRL (Certificate Revocation List)
- Cascade revoke for delegated capabilities
- Session termination revokes all derived capabilities
- Revocation is eventually consistent across federation
