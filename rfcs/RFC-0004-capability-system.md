# RFC-0004: Capability System

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the capability-based security model for all SovereignStack operations.

## Motivation

Following Principle 6 — Capability-based Security, every action must require an explicit, revocable, and auditable capability.

## Specification

### Capability Structure

```json
{
  "uri": "capability://delegated:read:memory://xyz",
  "type": "capability",
  "version": "1.0.0",
  "granted_by": "node://issuer",
  "granted_to": "agent://recipient",
  "permissions": ["read", "list"],
  "target": "memory://xyz",
  "conditions": {
    "max_uses": 10,
    "expires_at": "2026-06-30T23:59:59Z",
    "allowed_jurisdictions": ["US", "EU"]
  },
  "signature": "..."
}
```

### Capability Types

- **Direct** — Explicit grant from resource owner
- **Delegated** — Transferred from another capability holder
- **Derived** — Automatically granted from parent session

### Capability Rules

1. No capability = No access
2. Capabilities can be revoked at any time
3. Delegation depth is bounded (max 3 levels)
4. Capabilities expire by default (max 24h for delegated)
5. All capability use is audited

### Verification Flow

1. Extract capability URI from request
2. Verify cryptographic signature
3. Check expiration and conditions
4. Check revocation status
5. Grant or deny access

## Security Considerations

- Revocation uses a distributed revocation list
- Capability tokens are bearer tokens (must be transmitted securely)
- Session termination revokes all derived capabilities

## Reference Implementation

- ss-capability crate: `crates/ss-capability/src/capability.rs`
