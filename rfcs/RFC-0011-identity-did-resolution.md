# RFC-0011: Identity & DID Resolution

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0002

## Summary

Defines how SovereignStack nodes resolve Decentralized Identifiers (DIDs) into agent/node identity objects, including key rotation, multi-sig wallets, and cross-fabric DID anchoring.

## Specification

### DID Method

`sov:<namespace>:<specific-id>` — e.g., `did:sov:zcube-a:node-gpu-003`

### Resolution Flow

1. Parse DID → extract namespace + specific-id
2. Check local registry cache (LRU, TTL 300s)
3. On miss: query fabric DISCOVER (RFC-0032) or fallback to federation
4. Return identity document with public keys, endpoints, jurisdiction

### Identity Document

```json
{
  "id": "did:sov:zcube-a:node-gpu-003",
  "controller": "did:sov:zcube-a:admin",
  "verification_method": [
    {"id": "#key-1", "type": "Ed25519VerificationKey2020", "publicKeyMultibase": "z6Mk..."}
  ],
  "authentication": ["#key-1"],
  "capability_invocation": ["#key-1"],
  "services": [{"id": "#afp", "type": "AiFabricProtocol", "endpoint": "afp://node-gpu-003:8546"}]
}
```

## Core Types

`IdentityDocument`, `DidResolver`, `KeyRotationPolicy`
