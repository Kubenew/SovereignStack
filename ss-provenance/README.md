# ss-provenance

Tamper-evident cryptographic provenance chains and evidence generation for SovereignStack.

## Status: Implemented

Every action in SovereignStack is recorded in a provenance chain. Each entry is
cryptographically linked to the previous entry via SHA-256 hashing, creating an
immutable audit log signed with Ed25519 keys.

## Components

| Module | Purpose |
|--------|---------|
| `chain.rs` | `ProvenanceChain` — append-only, hash-linked chain with linkage enforcement |
| `entry.rs` | `ProvenanceEntry` — action record with canonical serialization, content hashing, and Ed25519 signing |
| `evidence.rs` | `EvidencePackage` — self-contained evidence bundle binding a chain to a conformance profile |
| `verifier.rs` | `ChainVerifier` — full chain verification: linkage integrity, signature validation, root hash check |

## Core Contract Claims

- **PROV-CHAIN-001**: Provenance chains enforce hash linkage between entries
- **PROV-ENTRY-001**: Entries are signed with Ed25519 and include canonical content hashes
- **PROV-EVIDENCE-001**: Evidence packages are independently verifiable
- **PROV-VERIFY-001**: Chain verifier detects tampering (broken links, invalid signatures, root hash mismatch)

## Integration

- **ss-kernel**: `ProvenanceService` trait + `ProvenanceServiceImpl` (see `ss-kernel/src/provenance.rs`)
- **reference-node**: HTTP API at `/provenance/record`, `/provenance/chain`, `/provenance/verify`, `/provenance/evidence`

## Usage

```rust
use ss_provenance::{ProvenanceChain, ProvenanceEntry, ProvenanceAction, ChainVerifier};
use ss_core::SovereignUri;

let mut chain = ProvenanceChain::new();
let entry = ProvenanceEntry::new(
    ProvenanceAction::Created,
    SovereignUri::parse("agent://alice").unwrap(),
    SovereignUri::parse("knowledge://doc-1").unwrap(),
    None,
    &serde_json::json!({"content": "hello"}),
);
chain.append(entry).unwrap();
```
