# SovereignStack

**An open protocol and reference implementation for verifiable, policy-governed AI infrastructure.**

## Current Milestone: v0.5 — Core Contract

The v0.5 Core Contract defines the minimum verifiable protocol for sovereign AI nodes:

```
Identity → Capability → Policy → Action → Provenance → Evidence
```

| Core Service | Crate | Status |
|-------------|-------|--------|
| Identity | `ss-identity`, `ss-crypto` | Implemented |
| Capability | `ss-capability` | Implemented |
| Policy | `ss-policy` | Implemented |
| Events | `ss-eventbus` | Implemented |
| Provenance | `ss-provenance` | Implemented |
| Kernel | `ss-kernel` | Implemented (7 services) |
| Reference Node | `reference-node` | Implemented |

See [registry/components.yaml](registry/components.yaml) for machine-readable, component-by-component status.

## Quick Start

```bash
git clone https://github.com/Kubenew/SovereignStack.git
cd SovereignStack
cargo build --release
./target/release/ss-node --port 8546
```

## Golden Path Demo

Run the Morpheus governed-infrastructure golden path in one command —
no Morpheus instance required (uses reference fixtures):

```bash
bash demo/morpheus/run.sh        # Linux/macOS (PowerShell: .\demo\morpheus\run.ps1)
```

The demo walks the full governance pipeline: **Discover → Authorize → Execute →
Provenance → Evidence → Independent Verify**, and prints `STATUS: CONFORMANT`
when the evidence package independently verifies. See
[`demo/morpheus/`](demo/morpheus/) and [`integrations/morpheus/`](integrations/morpheus/).

## Verify

Run the one-command verification gate — builds the reference node and enforces
the 7 Core Contract vectors:

```bash
bash verify.sh
```

For step-by-step manual verification (see [`v0.5-Verification-Gate.md`](v0.5-Verification-Gate.md)):

```bash
# Rust workspace tests
cargo test --workspace

# Run the Python conformance harness against the node
pip install -r requirements/conformance.txt
python tools/ss-conformance.py --endpoint http://localhost:8546 --profile core-0.1
```

## Conformance

The Core Contract is verified against 7 deterministic test vectors:

| Vector | Description |
|--------|-------------|
| `identity-creation` | Ed25519 identity generation and verification |
| `object-signing` | Cryptographic object signing and hash verification |
| `capability-grant` | Capability registration, grant, and revocation |
| `policy-evaluation` | Policy rule matching and enforcement |
| `event-integrity` | Event publish/subscribe with integrity |
| `provenance-chain` | Hash-linked provenance chain creation and tamper detection |
| `evidence-generation` | Evidence package generation with conformance profile binding |

See [conformance/profiles/core-node.yaml](conformance/profiles/core-node.yaml) for the formal profile definition.

## Status

Build: ![Build](https://github.com/Kubenew/SovereignStack/actions/workflows/ci.yml/badge.svg)

> **Note**: OASA certification levels (L1/L2/L3) are defined as a *specification*.
> No implementation has yet been independently certified. See [CONFORMANCE.md](CONFORMANCE.md).

## Vision: Internet for Intelligence

SovereignStack's long-term vision is to become the foundational protocol for sovereign,
distributed intelligence. See the [vision/](vision/) directory for the research roadmap
and [ROADMAP.md](ROADMAP.md) for the implementation timeline.

## Documentation

- [Architecture](ARCHITECTURE.md) — System architecture and layer model
- [Conformance](CONFORMANCE.md) — OASA certification specification
- [Components](registry/components.yaml) — Component registry with maturity status
- [Claims](registry/claims.yaml) — Verifiable claims with evidence mapping
- [ADR-0001](docs/adr/ADR-0001-architecture-layer-model.md) — Architecture decision record
- [Contributing](CONTRIBUTING.md) — How to contribute
