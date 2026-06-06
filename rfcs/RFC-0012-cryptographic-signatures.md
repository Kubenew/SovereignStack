# RFC-0012: Cryptographic Signatures & Verification

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001

## Summary

Defines the cryptographic primitives, signature formats, and verification chains used across all SovereignStack objects.

## Specification

### Required Algorithms

| Algorithm | Purpose | Key Length |
|-----------|---------|------------|
| Ed25519 | Object signing, identity keys | 32 bytes seed |
| SHA-256 | Content hashing, merkle trees | 256-bit digest |
| AES-256-GCM | Payload encryption (at-rest) | 256-bit key |
| BLAKE3 | Fast content addressing (optional) | 256-bit digest |

### Signature Envelope

```json
{
  "algorithm": "ed25519",
  "public_key": "z6Mk...",
  "signature": "base64url...",
  "signed_at": "2026-06-03T12:00:00Z",
  "payload_hash": "sha256:abc123..."
}
```

### Verification Chain

Every object references its parent via `audit.previous_hash`, forming a hash chain. Root objects are anchored to a genesis block signed by the node operator.
