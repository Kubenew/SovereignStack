# 01 — ss-kernel: Core System Kernel

**Layer:** Kernel
**Status:** Draft
**Source:** `ss-kernel/`

## Responsibilities

The kernel is the **only mandatory component** of any SovereignStack node. It provides six core services:

### 1. Identity Service

- Generate and manage Ed25519 key pairs
- Issue node and agent identity certificates
- Verify signatures on all inbound objects
- Maintain the local identity registry

### 2. URI Resolver

- Resolve `agent://`, `session://`, `memory://`, `knowledge://`, `capability://`, `policy://`, `node://` URIs
- Local-first resolution (RFC-0002)
- Cache resolved objects for configurable TTL

### 3. Event Bus

- Publish/subscribe event system for all state changes
- Events are immutable and signed
- Supports event sourcing for full audit trails

### 4. Object Registry

- Local store of all known objects
- CRUD operations with capability enforcement
- Indexed by URI, type, owner, and tags

### 5. Capability Enforcer

- Intercept all operations
- Verify caller holds required capability
- Reject with 403 if capability missing
- Log all capability grants and revocations

### 6. Policy Engine

- Evaluate governance policies against operations
- Support jurisdiction filtering
- Enforce data residency rules
- Audit policy decisions

## Interfaces

```rust
pub trait Kernel {
    fn identity(&self) -> &dyn IdentityService;
    fn resolver(&self) -> &dyn UriResolver;
    fn event_bus(&self) -> &dyn EventBus;
    fn registry(&self) -> &dyn ObjectRegistry;
    fn capabilities(&self) -> &dyn CapabilityEnforcer;
    fn policy(&self) -> &dyn PolicyEngine;
}
```

## Dependencies

- `ss-crypto` — Ed25519, SHA-256, Merkle proofs
- `ss-types` — Common types, URIs, errors

## Non-Responsibilities

The kernel does **not** handle:
- AI model inference
- Agent reasoning
- Memory persistence beyond cache
- Network discovery
- Swarm coordination

These are handled by upper layers.
