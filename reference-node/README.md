# SovereignStack Reference Node

**Status:** Experimental
**Version:** 0.1.0

## Overview

The SovereignStack Reference Node is a minimal, runnable implementation of the core SovereignStack architecture. It assembles the kernel services (identity, URI resolution, event bus, object registry, capability enforcement, policy engine) into a single binary with a SIP-compatible endpoint.

**No AI. No swarm. No federation.** Just the core architecture.

## Quick Start

```bash
cargo build -p sovereignstack-reference-node

cargo run -p sovereignstack-reference-node -- --name my-node --port 8546
```

## Features

| Feature | Flag | Status |
|---------|------|--------|
| Kernel (identity, resolver, eventbus, registry, capability, policy) | default | ✅ |
| Session daemon | `--with-sessiond` | 🚧 Planned |
| Content-addressed storage | `--with-cas` | 🚧 Planned |
| Federation | — | Future |
| AI inference | — | Future |

## Architecture

```
ss-node
 └── ss-kernel
      ├── Identity Service
      ├── URI Resolver
      ├── Event Bus
      ├── Object Registry
      ├── Capability Enforcer
      └── Policy Engine
```

## SIP Endpoint

The node exposes a SIP (Sovereign Intelligence Protocol) endpoint:

- WebSocket: `ws://host:port/sip/v1`
- HTTP: `http://host:port/sip/v1`

### Example

```bash
curl -s http://localhost:8546/sip/v1/ping
# → "pong"
```
