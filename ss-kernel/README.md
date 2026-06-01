# ss-kernel

**Status:** Draft
**Version:** 0.1.0

SovereignStack Kernel — core system services that every node must provide.

## Services

- **Identity Service** — Ed25519 key generation, certificate management, signature verification
- **URI Resolver** — Local-first resolution with federated fallback (RFC-0002)
- **Event Bus** — Publish/subscribe with immutable, signed events for event sourcing
- **Object Registry** — Local store of all known objects indexed by URI, type, owner, tags
- **Capability Enforcer** — Intercept all operations, verify capabilities before allowing access
- **Policy Engine** — Evaluate governance policies, enforce jurisdiction and data residency rules

## Usage

```rust
use ss_kernel::{
    Kernel,
    identity::IdentityServiceImpl,
    resolver::UriResolverImpl,
    eventbus::EventBusImpl,
    registry::ObjectRegistryImpl,
    capability::CapabilityEnforcerImpl,
    policy::PolicyEngineImpl,
};
```

## Dependencies

- `ss-crypto` — Ed25519, SHA-256
- `ss-core` — Common types, URIs, timestamps
