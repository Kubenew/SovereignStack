# SovereignStack

**The open governance and verification layer for autonomous infrastructure.**

> **SovereignStack v0.6 introduces Governed Autonomous Action: a vendor-neutral protocol for authorizing, executing, recording, and independently verifying AI-driven infrastructure operations.**

---

```text
                         AI AGENTS
               (Claude, Astra, Custom LLMs)
                            │
                            │ Action Request
                            ▼
              ┌─────────────────────────┐
              │      SOVEREIGNSTACK     │
              │                         │
              │ Identity & Workload DID │
              │ Capability Scoping      │
              │ Policy Evaluation       │
              │ Pre-Action Auth Token   │
              │ Action Envelope         │
              │ Provenance Graph        │
              │ Cryptographic Evidence  │
              │ Independent Verifier    │
              └────────────┬────────────┘
                           │ target://scheme
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    MORPHEUS            HARNESS          KUBERNETES
REFERENCE/FIXTURE       Adapter          Adapter
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Fixture / Live Mode │
                 └─────────────────────┘
                           │
                           ▼
                    INFRASTRUCTURE
              (Clouds, Bare Metal, Networks)
                           │
                           ▼
                    PROVIDER EVIDENCE
                           │
                           ▼
                  INDEPENDENT VERIFY
```

> **"One governance protocol. Multiple execution environments. Independently verifiable actions."**

---

## The Golden Path

Every governed autonomous action strictly adheres to the 5-stage Golden Path:

```text
AI Agent ──► DISCOVER ──► AUTHORIZE ──┬──► [DENY] ──► RECORD DENIAL (Provider execution = 0)
                                      │
                                      └──► [ALLOW] ──► EXECUTE (Adapter dispatch via target://)
                                                          │
                                                          ▼
                                                        RECORD (Action Envelope + Provider Audit)
                                                          │
                                                          ▼
                                                        VERIFY (Independent cryptographic proof)
```

1. **DISCOVER**: Query actor capabilities, supported target schemes, and active policies.
2. **AUTHORIZE**: Evaluate action intent against organizational policies; issue a single-use authorization token. Denied actions halt immediately with zero provider execution.
3. **EXECUTE**: Present authorization token to dispatch execution to the target platform adapter (`target://morpheus`, `target://k8s`, `target://harness`).
4. **RECORD**: Ingest native execution telemetry, bi-directionally bind provider action IDs, and construct a signed [Action Envelope](schemas/action-envelope.schema.json).
5. **VERIFY**: Third-party verifiers independently validate digital signatures, hash chains, and provider audit evidence.

---

## 3-Minute Flagship Demo

Experience the two-action showcase in one command:

```bash
python demo/morpheus/run_v06_demo.py        # Windows / Linux / macOS
# Or PowerShell: .\demo\morpheus\run_v06_demo.ps1
```

### What the demo showcases:
1. **Dangerous Action (Anti-Theater Gate):** A support agent requests `DELETE production-db-01`. Policy issues **`DENY`**. **Provider actions executed: 0.** A cryptographic denial evidence envelope is generated and verified.
2. **Legitimate Governed Action:** The agent requests `RESTART staging-web-01`. Policy issues **`ALLOW`** with a single-use token. Morpheus executes the safe operation, returns a native task ID, and binds it to the OASA Action Envelope.
3. **Independent Cryptographic Verification:** The resulting evidence package is verified offline with Ed25519 signature verification and hash integrity checks (**`PASS`**).
4. **Normative Conformance:** The automated test harness runs the full 16-test suite (**`16/16 PASS — STATUS: OASA-CONFORMANT`**).

---

## Normative Conformance Test Harness

Run the official OASA Conformance Suite to validate protocol compliance:

```bash
python tools/oasa_conformance.py --profile profiles/core/0.1.yaml
```

```text
================================================================
OASA CONFORMANCE HARNESS — Profile: profiles/core/0.1.yaml
================================================================
  [PASS] AUTH-001 AuthorizationPrecedesExecution
  [PASS] AUTH-002 TestUnauthorizedActionNeverReachesProvider
  [PASS] AUTH-003 TestAuthorizationTokenExpires
  [PASS] AUTH-004 TestAuthorizationTokenCannotBeReplayed
  [PASS] AUTH-005 TestCapabilityCannotBeEscalated
  [PASS] AUTH-006 TestTargetCannotBeChangedAfterAuthorization
  [PASS] ENV-001  TestActionEnvelopeHasUniqueId
  [PASS] ENV-002  TestActorIsAttributable
  [PASS] ENV-003  TestCapabilityIsExplicit
  [PASS] ENV-004  TestTargetIsExplicit
  [PASS] DEL-001  TestDelegationChainIsPreserved
  [PASS] DEL-002  TestInvalidDelegationIsRejected
  [PASS] PROV-001 TestProviderActionIdIsLinked
  [PASS] EVID-001 TestAuthorizedActionProducesVerifiableEvidence
  [PASS] EVID-002 TestTamperedEvidenceFailsVerification
  [PASS] EVID-003 TestAuthorizedActionMustHaveProviderEvidence
----------------------------------------------------------------
Summary: 16/16 Passed (100%)
STATUS: OASA-CONFORMANT
----------------------------------------------------------------
```

> **OASA-CONFORMANT** means that the SovereignStack reference implementation passes the normative requirements of the declared OASA profile using the specified conformance harness. It does not imply independent certification, vendor endorsement, or live-provider validation unless explicitly stated.

---

## How SovereignStack Complements Existing Infrastructure

We do not replace the existing infrastructure ecosystem. We make autonomous actions across it governable and independently verifiable:

| System | Primary Role | SovereignStack Relationship |
| :--- | :--- | :--- |
| **Kubernetes** | Compute orchestration | Govern workload operations |
| **Terraform / OpenTofu** | Infrastructure provisioning | Govern Terraform actions |
| **Harness** | Software delivery / CI/CD | Govern deployment pipelines |
| **HPE Morpheus** | Multi-cloud infrastructure orchestration | **First reference adapter (`target://morpheus`)** |
| **OPA / Cedar** | Policy decisions | Pluggable policy engines |
| **OpenTelemetry (OTel)** | Observability / Tracing | Operational evidence telemetry |
| **SIEM (Splunk/Sentinel)** | Security monitoring | Consume verifiable audit envelopes |

See [docs/ECOSYSTEM_COMPLEMENTARITY_MEMO.md](docs/ECOSYSTEM_COMPLEMENTARITY_MEMO.md) for the complete partner strategy.

---

## Traction & Maturity Status

To preserve credibility with technical evaluators, partners, and investors, SovereignStack maintains brutal transparency regarding implementation maturity:

- **Specification:** [OASA v0.6 Specification](specs/OASA-CORE-v0.6-SPEC.md) (Draft Normative Standard).
- **Core Engine:** Reference Python / Rust implementation with atomic server-side token lease state and Ed25519 canonical signing.
- **Reference Adapter:** Morpheus reference adapter with fixture-backed provider execution and evidence binding (`integrations/morpheus/adapter/morpheus_adapter.py`).
- **Conformance:** Passing automated test suite grants **`OASA-Conformant`** status. Formal **`OASA-Certified`** status is reserved for future accredited third-party validation programs. SovereignStack reference implementation passes all 16 OASA Core v0.6 conformance tests.
- **Commercial Status:** Open-source foundation under the [OASA Constitution](CONSTITUTION.md). Design-partner phase underway.

---

## Documentation

- [Constitution](CONSTITUTION.md) — The OASA Foundation Charter and Fail-Closed Axiom
- [Strategic Investor One-Pager](docs/STRATEGIC_INVESTOR_ONE_PAGER.md) — Market positioning and defensible moat
- [Ecosystem Architecture Memo](docs/ECOSYSTEM_COMPLEMENTARITY_MEMO.md) — Infrastructure platform complementarity
- [OASA Core Contract Spec](specs/OASA-CORE-v0.6-SPEC.md) — Formal v0.6 protocol specification
- [Authoritative Profile](profiles/core/0.1.yaml) — Frozen Core 0.1 profile definition
- [Action Envelope Schema](schemas/action-envelope.schema.json) — Formal JSON Schema for Governed Actions
- [Conformance Framework](CONFORMANCE.md) — Conformance and certification requirements
- [Roadmap](ROADMAP.md) — Implementation milestones through v1.0
