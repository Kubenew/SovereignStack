# SovereignStack Architecture Overview

**Document:** 00-overview.md
**Layer:** Meta
**Status:** Stable

## System Context

SovereignStack is a distributed operating system for intelligence. It defines the protocol stack, object model, and runtime for a global network of sovereign intelligent agents.

## Architecture Principles

1. **Everything is an Object** — Agents, memories, knowledge, capabilities, and policies all share a common object model (RFC-0001).
2. **Everything has a URI** — Every object is globally addressable and resolvable (RFC-0002).
3. **Everything is Verifiable** — All objects are cryptographically signed with full provenance.
4. **Capability-Based Security** — No implicit trust; all actions require explicit capabilities.
5. **Offline First** — Local resolution preferred; federation is opt-in.
6. **Human Override** — Human governance is always possible.

## System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                   APPLICATIONS & TOOLS                        │
│  Dashboard │ CLI │ SDK (Python/TS/Go) │ Workflow Engine      │
├──────────────────────────────────────────────────────────────┤
│                   SS-KERNEL (Core)                            │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │Identity  │ │URI       │ │Event Bus │ │Object Registry   │ │
│  │Service   │ │Resolver  │ │          │ │                  │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌─────────┐ ┌──────────┐ ┌──────────────────────────────┐  │
│  │Capability│ │Policy    │ │Crypto (Ed25519, SHA-256)    │  │
│  │Enforcer  │ │Engine    │ │                              │  │
│  └─────────┘ └──────────┘ └──────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                        │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐   │
│  │ss-cas    │ │ss-federation │ │ss-trust  │ │ss-policy │   │
│  │(Storage) │ │(Discovery)   │ │(Graph)   │ │(Govern.) │   │
│  └──────────┘ └──────────────┘ └──────────┘ └──────────┘   │
├──────────────────────────────────────────────────────────────┤
│                   INTELLIGENCE LAYER                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │ss-reason│ │ss-kas  │ │ss-mem  │ │ss-twin │ │ss-swarm  │  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘  │
├──────────────────────────────────────────────────────────────┤
│                   ORCHESTRATION LAYER                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐                 │
│  │ss-sched  │ │ss-routing│ │ss-discovery  │                 │
│  └──────────┘ └──────────┘ └──────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

## Layer Summary

| Layer | Components | Responsibility |
|-------|------------|----------------|
| Kernel | Identity, URI Resolver, Event Bus, Object Registry, Capability Enforcer, Policy Engine | Core system services |
| Infrastructure | CAS, Federation, Trust, Policy | Distributed system primitives |
| Intelligence | Reason, KAS, Memory, Twin, Swarm | AI/ML capabilities |
| Orchestration | Scheduler, Routing, Discovery | Coordination |

## Key Protocols

- **SIP** — Sovereign Intelligence Protocol (inter-node communication)
- **SEP** — Sovereign Extension Protocol (plugin system)
- **SAP** — Sovereign Agent Protocol (agent lifecycle)
- **SMP** — Sovereign Memory Protocol (memory operations)
- **KAP** — Sovereign Knowledge Access Protocol (knowledge queries)
- **REP** — Sovereign Reasoning Exchange Protocol (reasoning traces)

## Related Documents

- [01-kernel.md](01-kernel.md) — Kernel specification
- [02-session-runtime.md](02-session-runtime.md) — Session lifecycle
- [03-identity.md](03-identity.md) — Identity system
- [04-memory.md](04-memory.md) — Memory hierarchy
- [05-federation.md](05-federation.md) — Federation model
- [06-capabilities.md](06-capabilities.md) — Capability system
- [07-governance.md](07-governance.md) — Governance & policy
- [08-trust.md](08-trust.md) — Trust graph
- [09-sip.md](09-sip.md) — SIP protocol details
