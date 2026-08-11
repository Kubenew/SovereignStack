# SovereignStack

**An open protocol and reference implementation for verifiable, sovereign AI nodes.**

v0.5 demonstrates the core contract: `identity -> capability -> policy -> provenance -> evidence`.

## Quick Start
```bash
git clone https://github.com/SovereignStack/SovereignStack.git
cd SovereignStack
cargo build --release
./target/release/ss-node --port 8546
```

## Verify
```bash
cargo test --workspace
# Run the Python conformance harness against the node
python tools/ss-conformance.py --endpoint http://localhost:8546 --profile core-0.1
```

## Status
Build: ![Build](https://github.com/SovereignStack/SovereignStack/actions/workflows/ci.yml/badge.svg)
Conformance: ![OASA L1](badges/oasa-l1.svg)

See [registry/components.yaml](registry/components.yaml) for a machine-readable, component-by-component status indicating what is implemented vs stubbed.
See the `vision/` directory for the long-term project roadmap and research documents.
