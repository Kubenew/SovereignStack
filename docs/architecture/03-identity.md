# 03 — Identity System

**Layer:** Kernel
**Status:** Draft
**Source:** `ss-identity/`, `ss-sig/`

## Overview

Every entity in SovereignStack has a cryptographic identity. Identity is the foundation of trust, capabilities, and provenance.

## Identity Types

| Type | URI Prefix | Key Type | Lifespan |
|------|------------|----------|----------|
| Node | `node://` | Ed25519 | Permanent |
| Agent | `agent://` | Ed25519 | Configurable |
| Organization | `org://` | Ed25519 | Permanent |
| Device | `robot://` | Ed25519 | Hardware-bound |

## Identity Document

```json
{
  "uri": "agent://a1b2c3d4",
  "public_key": "ed25519:dead...beef",
  "algorithm": "Ed25519",
  "created_at": "2026-05-31T00:00:00Z",
  "expires_at": "2027-05-31T00:00:00Z",
  "metadata": {
    "name": "researcher-1",
    "jurisdiction": "EU",
    "node": "node://home-node"
  },
  "signature": "sig:abc123..."
}
```

## Verification Flow

1. Present identity document + signature
2. Verify signature against public key
3. Check expiration
4. Check revocation status (via local CRL or OCSP-equivalent)
5. If valid, trust the identity

## Key Management

- Private keys never leave the node
- Keys can be rotated (new document issued)
- Lost keys = lost identity (re- registration required)
- Hardware-backed key storage (TPM 2.0) optional but recommended
