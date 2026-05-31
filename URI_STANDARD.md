# SovereignStack URI Standard

**Version:** 1.0
**Status:** Draft

## URI Schemes

```
agent://<uuid-or-did>
session://<session-id>
memory://<memory-id>
knowledge://<knowledge-id>
reason://<reason-trace-id>
artifact://<artifact-id>
workflow://<workflow-id>
capability://<capability-id>
policy://<policy-id>
node://<node-id>
```

## Resolution Rules

1. Local resolution preferred (Offline First)
2. Federation resolution only if explicitly allowed
3. All URIs are **case-sensitive**
4. DID (Decentralized Identifier) support planned

## Examples

- `agent://a1b2c3d4-e5f6-...`
- `knowledge://sha256:abc123...`
- `capability://delegated:read:memory://xyz`

This standard enforces **Principle 4 — Address Everything**.
