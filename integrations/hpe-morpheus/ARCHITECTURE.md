# HPE Morpheus Integration — Architecture

## Overview

The integration implements the SovereignStack **core contract** in front of the
HPE Morpheus REST API. Every Morpheus-affecting action passes through a
governance pipeline that produces a signed, tamper-evident provenance chain and
a verifiable evidence package.

Morpheus is never contacted unless the governing decision is ALLOW.

```
 agent://ml-platform (Ed25519 keypair)
        │
        │  signed request (action + spec + nonce)
        ▼
┌─────────────────── GOVERNANCE PIPELINE ───────────────────┐
│  1. IDENTITY      resolve agent://, verify request sig    │
│  2. CAPABILITY    capability:// present & granted         │
│  3. POLICY        policy://morpheus/* evaluated           │
│                   (conflict → safe-halt + escalate)       │
│  4. DECISION      ALLOW | DENY  (recorded either way)     │
└──────────────────────────┬────────────────────────────────┘
                  ALLOW    │    DENY
                           ▼
                 ┌───────────────────┐
                 │  HPE MORPHEUS     │   not called
                 │  POST /api/vms    │
                 └─────────┬─────────┘
                           │  vm-id
                           ▼
   provenance chain append (signed entry)  →  evidence:// package (signed)
```

## Components

### 1. Identity Binding — `adapter/identity_mapper.py`

- Maps Morpheus user/service-account names to SovereignStack `agent://` URIs.
- Maintains an agent registry: `agent://uri -> Ed25519 public key (hex)`.
- Verifies agent request signatures before any authorization work.

### 2. Capability Mapping — `adapter/capability_mapper.py`

- Maps Morpheus roles to `capability://` URIs.
- Enforces that the acting agent holds the requested capability before the
  policy stage, matching Morpheus RBAC semantics while adding cryptographic
  proof of the grant.

### 3. Policy Translation — `adapter/policy_translator.py`

- Loads versioned policy YAML catalogs from `policies/`.
- Evaluates rules over the request spec (cpu, memory, network, image,
  environment).
- **Safe-halt on conflict**: if policies produce inconsistent decisions, the
  engine denies and marks the result for human escalation (RFC-0075). It never
  guesses.

### 4. Event Listener — `adapter/event_listener.py`

- Captures Morpheus webhook/action events (provision, configure, delete).
- Each event is content-hashed and appended to the provenance chain, so
  asynchronous infrastructure events remain auditable too.

### 5. Provenance Chain — `provenance/morpheus_provenance_chain.py`

- Merkle-style linked chain: every entry stores `prev_hash`, `content_hash`,
  and an Ed25519 signature over its canonical form.
- `append` enforces linkage; `verify` recomputes hashes and validates
  signatures; tampering breaks verification at the exact entry.

### 6. Evidence — `evidence/evidence_generator.py` / `evidence_verifier.py`

- `EvidencePackage` wraps a decision, its chain, and metadata; it is signed by
  the governing node.
- The verifier is independent of Morpheus: it needs only the package and public
  keys. `ss-audit verify` semantics.

### 7. Governed Client — `api/morpheus_client.py`

- Orchestrates the pipeline for a single action:
  `govern(action, spec, agent, capability, signer)`.
- Returns `{decision, checks, morpheus_call, chain, evidence}`.

### 8. Mock Morpheus — `api/morpheus_mock.py`

- Stdlib `http.server` implementation exposing `/health`, `/api/auth/token`,
  and `POST /api/vms`. Used for demos and conformance tests; a real Morpheus
  instance can be substituted by pointing the client at its base URL.

## Security Properties

| Property               | Mechanism                                                |
|------------------------|----------------------------------------------------------|
| Authentication         | Ed25519 request signatures, verified against registry    |
| Authorization          | Capability grants + policy evaluation (RFC-0075)         |
| Tamper evidence        | Content-hash per entry; linkage across the chain         |
| Non-repudiation        | Per-entry signatures                                     |
| Replay resistance      | Per-request nonce, rejected on reuse                     |
| Safe default           | No rule / conflicting rules ⇒ DENY + escalate            |

## Extensibility

The control-plane adapter pattern is reusable. Kubernetes and VMware follow the
same five interfaces (identity, capability, policy, event, provenance), which is
the roadmap to the **Sovereign Infrastructure** certification level:

- `integrations/hpe-morpheus/`  (this integration — reference pattern)
- `integrations/kubernetes/`    (future)
- `integrations/vmware/`        (future)
