# OASA Core Contract & Architecture Specification (v0.6)

**Specification:** Open Architecture Specification for Governed Autonomous Action (OASA)  
**Version:** v0.6.0-draft  
**Status:** Normative Architecture Contract  

---

## 1. The Flagship Mission

> **SovereignStack v0.6 introduces Governed Autonomous Action: a vendor-neutral protocol for authorizing, executing, recording, and independently verifying AI-driven infrastructure operations.**

The protocol establishes a standardized trust boundary between autonomous AI agents and heterogeneous execution environments.

---

## 2. The Golden Path Lifecycle

Every governed autonomous action strictly adheres to the 5-stage Golden Path:

```text
  ┌──────────────┐
  │   DISCOVER   │  Query actor capabilities, target schemes, and active policy sets
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  AUTHORIZE   │  Evaluate intent against policy; issue single-use authorization token
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   EXECUTE    │  Present token; dispatch governed action to platform execution adapter
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │    RECORD    │  Ingest execution telemetry; bind provider action ID to OASA envelope
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │    VERIFY    │  Independently validate cryptographic signatures, hashes, and evidence
  └──────────────┘
```

---

## 3. Core API Architecture & Vendor Neutrality

The Core governance engine has **zero knowledge of specific infrastructure providers**. It does not execute cloud infrastructure directly. Instead, it dispatches execution to registered adapters using URI schemes (`target://scheme`):

```text
                      OASA CORE ENGINE
                             │
                      target://scheme
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     morpheus://...     harness://...     k8s://...
    Morpheus Adapter   Harness Adapter   K8s Adapter
       (Ref #1)           (Target)         (Target)
```

Adding a new execution platform requires only an adapter implementation conforming to the OASA Adapter Contract, without modifying the governance engine.

### API Endpoints

#### 1. `POST /discover`
Queries capabilities and constraints for a given actor and target.
- **Request:**
  ```json
  {
    "actor_did": "did:oasa:agent:ops-agent-01",
    "target_uri": "morpheus://cloud-east/vms"
  }
  ```
- **Response:**
  ```json
  {
    "supported_schemes": ["morpheus", "k8s", "harness"],
    "allowed_capabilities": ["vm:restart", "vm:status"],
    "restricted_capabilities": ["vm:delete", "network:reconfigure"]
  }
  ```

#### 2. `POST /authorize`
Evaluates action intent against organizational and jurisdictional policies.
- **Request:**
  ```json
  {
    "actor_did": "did:oasa:agent:ops-agent-01",
    "action": "vm:restart",
    "target_uri": "morpheus://cloud-east/vms/web-prod-01",
    "parameters": { "force": false },
    "context": {
      "rationale": "High memory pressure automated remediation",
      "incident_id": "INC-8821"
    }
  }
  ```
- **Response (ALLOW):**
  ```json
  {
    "decision": "ALLOW",
    "action_id": "act-01HZY88A72BC...",
    "authorization_token": "<signed_jwt_with_jti>",
    "expires_at": "2026-09-11T08:15:00Z"
  }
  ```
- **Response (DENY):**
  ```json
  {
    "decision": "DENY",
    "action_id": "act-01HZY88A99ZZ...",
    "denial_reason": "Policy violation: actor lacks production delete capability",
    "denial_evidence_id": "evi-denial-01HZY88A..."
  }
  ```

#### 3. `POST /execute`
Submits an authorized action for execution by presenting the single-use token.
- **Request:**
  ```json
  {
    "action_id": "act-01HZY88A72BC...",
    "authorization_token": "<signed_jwt_with_jti>",
    "target_uri": "morpheus://cloud-east/vms/web-prod-01",
    "payload": { "force": false }
  }
  ```
- **Execution Mechanism:** Core validates the token, atomically consumes it in server state, identifies the adapter from `morpheus://`, and invokes the adapter.
- **Response:**
  ```json
  {
    "status": "EXECUTED",
    "action_id": "act-01HZY88A72BC...",
    "provider_action_id": "morph-task-99412",
    "adapter_status": "SUCCESS"
  }
  ```

#### 4. `POST /record`
Binds the execution outcome, provider action ID, and runtime telemetry into a canonical OASA Action Envelope.
- **Request:**
  ```json
  {
    "action_id": "act-01HZY88A72BC...",
    "provider_action_id": "morph-task-99412",
    "native_evidence": { "status": "restarted", "duration_ms": 4120 }
  }
  ```
- **Response:** Signed OASA Action Envelope with cryptographic digest and Merkle root.

#### 5. `POST /verify`
Stateless verification of an action envelope.
- **Request:**
  ```json
  {
    "envelope": { ... }
  }
  ```
- **Response:**
  ```json
  {
    "valid": true,
    "checks": {
      "envelope_signature": "VALID",
      "payload_digest": "MATCH",
      "authorization_binding": "CONFIRMED",
      "provider_link": "CONFIRMED"
    }
  }
  ```

---

## 4. Security & Cryptographic Integrity Requirements

The following normative requirements address and remediate prototype vulnerabilities:

### 4.1 Configured Key Management in `VerifyToken()`
- Tokens MUST be signed and verified using asymmetric cryptography (e.g., Ed25519 or ECDSA P-256) or configured enterprise symmetric keys loaded from secure environment/KMS configuration.
- Prototypes MUST NOT rely on static or hardcoded global placeholder keys. Unconfigured key verification must raise a fatal initialization error.

### 4.2 Server-Side Atomic Single-Use Token State
- A JWT format does not, by itself, enforce single-use semantics.
- The Core server MUST maintain an atomic token ledger (`TokenStateStore`) tracking token IDs (`jti`), issue timestamps, expiry, and consumption status (`consumed_at`).
- Consumption during `POST /execute` MUST be performed via an atomic Compare-And-Swap (CAS) or synchronized mutex lock to eliminate race conditions.
- Replaying a token MUST immediately return `409 Conflict` (`TOKEN_ALREADY_CONSUMED`), preventing duplicate infrastructure execution.

### 4.3 Cryptographic Envelope Signing (`SignEnvelope()`)
- Action envelopes MUST be canonically serialized (RFC 8785 JSON Canonicalization Scheme) and hashed using SHA-256.
- The resulting digest MUST be cryptographically signed using the Core's private key (Ed25519).
- Dummy signatures or empty payloads MUST be rejected.

### 4.4 Strict Envelope Verification (`VerifyEnvelope()`)
- Verification MUST compute the canonical digest of the envelope payload and verify the digital signature against the signing authority's registered public key.
- Acceptance of arbitrary non-empty signature strings is strictly prohibited. Any signature mismatch or payload modification MUST fail verification immediately.

---

## 5. Normative Conformance Test Suite (v0.6)

The initial conformance suite establishes 13 essential normative tests. Passing this suite awards **OASA-Conformant** status (reserving "OASA-Certified" for formal third-party programs).

### 5.1 The Anti-Theater Gate (P0 Killer Test)
#### `TestUnauthorizedActionNeverReachesProvider`
Verifies that SovereignStack acts as an active gate rather than a passive logger:
1. Agent requests `DELETE` on a production target.
2. Core checks identity (`PASS`) and capabilities (`FAIL`).
3. Core issues `DENY` decision.
4. Core attempts to query provider action records.
5. **Assertions:**
   - Decision == `DENY`
   - Provider actions executed == `0` (provider is never contacted)
   - Cryptographic denial evidence == `PRESENT` in audit log

### 5.2 The Verifiable Evidence Gate (P0 Killer Test)
#### `TestAuthorizedActionProducesVerifiableEvidence`
Verifies the complete Golden Path:
1. Agent requests safe action (`vm:restart` on staging).
2. Core issues `ALLOW` with a single-use authorization token.
3. `/execute` dispatches to Morpheus adapter.
4. Morpheus adapter records native task ID.
5. `/record` binds OASA action ID ↔ provider action ID.
6. `/verify` performs independent cryptographic verification.
7. **Assertions:**
   - Authorization: `PASS`
   - Execution: `PASS`
   - Provenance: `PASS`
   - Evidence: `PASS`
   - Verification: `PASS`

### 5.3 Core Invariant Tests
3. **`TestAuthorizeDoesNotExecute`**: Calling `/authorize` evaluates policy without triggering provider actions.
4. **`TestTokenAtomicSingleUse`**: Concurrent execution requests using the same token succeed exactly once; all concurrent and subsequent calls fail.
5. **`TestTokenExpiration`**: Tokens submitted after `expires_at` are rejected.
6. **`TestTargetImmutability`**: Altering `target_uri` between authorization and execution fails.
7. **`TestActorImmutability`**: Altering the presenting actor DID fails.
8. **`TestCapabilityEscalationBlocked`**: Invoking actions outside the granted capability scope fails.
9. **`TestActionUniqueId`**: Every action receives a globally unique, collision-resistant identifier (`act-...`).
10. **`TestProviderActionLinked`**: Native provider action IDs are bi-directionally bound to the OASA action ID.
11. **`TestEvidenceHashValidation`**: Hashing evidence payload matches the envelope claim.
12. **`TestEnvelopeSignatureValidation`**: Modifying any payload field invalidates the cryptographic signature.
13. **`TestVerificationDetectsTampering`**: Independent verifier rejects modified envelopes.

---

## 6. Execution Order & Implementation Roadmap

```text
OASA Core Contract (This Spec)
         ↓
Minimal Core Engine (Go/Rust: 5 API routes, atomic store, crypto signing)
         ↓
Normative Conformance Suite (13 tests verifying anti-theater & crypto invariants)
         ↓
Morpheus Reference Adapter (First live reference environment)
         ↓
Flagship 3-Minute Demo (Deny Prod -> Allow Staging -> Morpheus Exec -> Verifier Pass)
         ↓
Ecosystem & Partner Outreach (Enterprise buyers, Morpheus, Harness, K8s)
```
