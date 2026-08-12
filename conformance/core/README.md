# Core Contract Conformance Profile (core-0.1)

This directory contains the Core Contract conformance profile and its test vectors.

## Profile

The `core-0.1` profile defines the minimum requirements for a SovereignStack-compatible
node. It covers seven areas: identity, object model, capability, policy, events,
provenance, and evidence.

See [../profiles/core-0.1.yaml](../profiles/core-0.1.yaml) for the formal profile.

## Vectors

The seven deterministic test vectors validate each Core Contract requirement:

| Vector | File | Description |
|--------|------|-------------|
| IDENT-001 | `identity-creation.json` | Ed25519 identity creation and verification |
| OBJ-001 | `object-signing.json` | Object signing and hash verification |
| CAP-001 | `capability-grant.json` | Capability registration, grant, evaluation |
| POL-001 | `policy-evaluation.json` | Policy rule matching and enforcement |
| EVT-001 | `event-integrity.json` | Event publish/subscribe integrity |
| PROV-001 | `provenance-chain.json` | Provenance chain creation and tamper detection |
| EVID-001 | `evidence-generation.json` | Evidence package generation |

## Running

```bash
# Against a running reference node
python tools/ss-conformance.py --endpoint http://localhost:8546 --profile core-0.1

# Rust unit tests for the underlying crates
cargo test --workspace
```
