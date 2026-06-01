# SovereignStack v0.3.0 — "Constitution & Standards"

**Release Date:** June 15, 2026
**Tag:** v0.3.0
**Branch:** release/v0.3.0

---

## Overview

v0.3.0 marks SovereignStack's transition from a software project into a **standards ecosystem**. It launches the full governance + standards framework, 10 RFCs, architecture documentation, reference implementation, and conformance testing — establishing SovereignStack as a serious standards body in sovereign AI.

## What's New

### Standards Ecosystem
- **10 RFCs** (0001–0010) covering: Object Model, URI Standard, Trust Graph, Capability Registry, Knowledge Objects, Reasoning Objects, Event Bus, Federation Routing, Session Lifecycle, Conformance Framework
- **STANDARDS.md** — 6-layer standards framework
- **PROTOCOL_REGISTRY.md** — 7 protocols with lifecycle tracking
- **ROADMAP-2035.md** — 10-year vision

### Architecture
- **docs/architecture/** — 10-page architecture breakdown + SVG diagram
- **ss-kernel/** — Formal Rust crate: Identity, URI Resolver, Event Bus, Object Registry, Capability Enforcer, Policy Engine
- **reference-node/** — Minimal runnable node (`ss-node` binary)

### Conformance
- **conformance/** — Executable test suites for SIP, SEP, SAP, SMP
- **4 conformance profiles**: core-node (L1), federation-node (L2), knowledge-node (L2), agent-node (L2)
- **RFC-0010** defines the formal conformance framework with attestation format

### Governance
- **GOVERNANCE.md** — TSC structure, Conformance WG, Standards WG
- **CONTRIBUTING.md** — Updated with RFC process and standards ecosystem
- **ANNOUNCEMENT.md** — Release announcement

## RFC Index

| RFC | Title | Status |
|-----|-------|--------|
| 0001 | Sovereign Object Model | Draft |
| 0002 | URI Standard + ABNF Grammar | Draft |
| 0003 | Trust Graph | Draft |
| 0004 | Capability Registry | Draft |
| 0005 | Knowledge Objects | Draft |
| 0006 | Reasoning Objects | Draft |
| 0007 | Event Bus | Draft |
| 0008 | Federation Routing | Draft |
| 0009 | Session Lifecycle | Draft |
| 0010 | Conformance Framework | Draft |

## Quick Start

```bash
# Clone and build
git clone https://github.com/Kubenew/SovereignStack.git
cd SovereignStack
cargo build --workspace

# Run reference node
cargo run -p sovereignstack-reference-node -- --name my-node --port 8546

# Run conformance tests
python -m pytest conformance/tests/ -v
```

## Stats

- **108+ files** changed across the release cycle
- **~8,400 lines** added (standards + architecture + kernel + tests)
- **10 RFCs** published
- **13 Rust crates** + Python/TS/Go bindings
- **4 conformance profiles**
- **License:** Apache 2.0

## Links

- [Release Branch](https://github.com/Kubenew/SovereignStack/tree/release/v0.3.0)
- [Architecture Docs](https://github.com/Kubenew/SovereignStack/tree/main/docs/architecture/)
- [RFCs](https://github.com/Kubenew/SovereignStack/tree/main/rfcs)
- [Conformance](https://github.com/Kubenew/SovereignStack/tree/main/conformance)
- [Reference Node](https://github.com/Kubenew/SovereignStack/tree/main/reference-node)

---

*"Sovereignty remains local while collaboration becomes seamless."*
