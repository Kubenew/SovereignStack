# RFC-0026: Capability Delegation Chain

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0004

## Summary

Defines how capabilities are delegated, scoped, revoked, and verified across agent chains — enabling fine-grained, revocable permission propagation.

## Specification

### Delegation Record

```json
{
  "id": "cap-deleg://abc123",
  "parent": "capability://write-knowledge",
  "delegate_to": "agent://sub-agent-5",
  "scope": {"jurisdictions": ["EU"], "max_ttl_secs": 3600, "max_depth": 2},
  "conditions": {"require_human_approval": true, "max_cost": 0.05},
  "issued_at": "2026-06-03T12:00:00Z",
  "expires_at": "2026-06-03T13:00:00Z",
  "signature_chain": ["ed25519:parent_sig...", "ed25519:delegate_sig..."]
}
```

### Chain Verification

Each delegation is verified by walking the chain to a root capability issued by the resource owner. Depth is bounded by `max_depth`.

### Core Types

`CapabilityDelegation`, `DelegationChain`, `DelegationScope`, `RevocationRecord`
