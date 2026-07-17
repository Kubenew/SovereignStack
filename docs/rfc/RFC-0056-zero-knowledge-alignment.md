# RFC-0056: Zero-Knowledge Alignment Proofs

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `values://` |
| Depends On | RFC-0010, RFC-0046 |
| Module | `ss-policy/src/zk_alignment.rs` |

## Overview

Agents prove alignment with organizational values without revealing
sensitive internal state, using a ZK-SNARK style proof structure.

## Proof Structure

```
ZkAlignmentProof {
    values_hash: [u8; 32],       // commitment to values document
    decision_digest: [u8; 32],   // hash of the proposed action
    proof_blob: Vec<u8>,         // zero-knowledge proof
    public_inputs: Vec<u8>,      // shared public parameters
}
```

## gRPC Integration

The `AlignmentStreamer` (RFC-0057) carries `ZkAlignmentProofMessage`
over the MindSync channel for real-time verification.

## Implementation

- `ss-policy/src/zk_alignment.rs` — Rust proof structures
- `scripts/generate_alignment_proof.py` — Python proof generator
- `ss-policy/src/proof_verifier.rs` — verifier with human override
