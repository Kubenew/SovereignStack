# RFC-0076: OASA Continuous Assurance Engine (CAE)

**Status:** Draft | **Type:** Standard | **Created:** 2026-08-07 | **Depends On:** RFC-0013, RFC-0022, RFC-0075  
**Related:** [OASA](../OASA.md), [CERTIFICATION](../CERTIFICATION.md)

## Abstract

Defines the **Continuous Assurance Engine (CAE)** — the component that transforms OASA from a "certified at a point in time" system into a system that **proves compliance continuously**. The CAE continuously maps observed system behavior to regulatory and internal control frameworks and produces a machine-verifiable **Assurance State**.

The CAE is the technical backbone of OASA's commercial value proposition: instead of a PDF once a year, an auditor (or regulator) gets a cryptographically signed, continuously updated attestation that the system is — and was — compliant at every instant.

## Motivation

Traditional compliance is episodic: an audit happens, evidence is gathered, a report is issued, and the system drifts until the next audit. For autonomous systems that make thousands of decisions per second, this is insufficient:

- A violation can occur and be "fixed" between audits — invisible to the auditor.
- Evidence is collected manually and is therefore incomplete and untrustworthy.
- Regulators increasingly require **ongoing** evidence (DORA's oversight of ICT risk, MiCA's reserve requirements, EU AI Act's post-market monitoring).

The CAE closes the gap between "we were compliant on audit day" and "we are compliant now."

## Specification

### 1. CAE Architecture

The CAE has five logical components:

```
┌─────────────────────────────────────────────────────────┐
│                    CAE (Continuous Assurance Engine)      │
│                                                          │
│  ┌───────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ Evidence  │  │  Framework  │  │    Continuous     │   │
│  │   Lake    │→│   Mapper    │→│    Assessor       │   │
│  └───────────┘  └─────────────┘  └──────────────────┘   │
│                         │               │               │
│                  ┌──────┴──────┐  ┌─────┴──────────┐    │
│                  │ Assurance   │  │ Continuous      │    │
│                  │  Packager   │  │ Attestation API │    │
│                  └─────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 2. Evidence Lake

A tamper-evident store of all evidence produced by the system, keyed by Merkle-ordered provenance (RFC-0013, RFC-0018):

- Every governed action emits evidence: authorization decisions, conflict resolutions (`conflict://` per RFC-0075), capability grants, data flows, model invocations.
- Evidence is immutable: appended, never edited; deletion is a signed tombstone event.
- Evidence is addressable and exportable: any audit question reduces to "retrieve and verify evidence for range [t₀, t₁]."

**Evidence record:**

| Field | Description |
|-------|-------------|
| `id` | Content-addressed evidence ID |
| `type` | `authorization` / `conflict` / `override` / `execution` / `dataflow` |
| `object` | The subject object (`agent://`, `workflow://`, ...) |
| `timestamp` | Signed monotonic time |
| `payload` | Canonical JSON payload |
| `merkle_proof` | Inclusion proof in the evidence chain |

### 3. Framework Mapper

Maps evidence types to control requirements of a target framework. Frameworks are declared as **control catalogs**:

- **Regulatory:** DORA, MiCA, EU AI Act, NIS2, GDPR
- **Industry:** ISO 27001, ISO 42001, SOC 2, PCI DSS, TLPT (Threat-Led Penetration Testing)
- **Internal:** organizational control libraries

Each control catalog entry declares:

```
control:
  id: "DORA-ART-11"
  requirement: "Detection and response to ICT-related incidents"
  evidence_type: "incident_response"
  threshold: "response_time < 30s"
  cadence: "continuous"
```

The mapper is **explicit and versioned** — a mapping change is itself an auditable event, so "the framework said we were compliant" is always reproducible.

### 4. Continuous Assessor

Evaluates live evidence against mapped controls:

- **Per-control evaluation** — for every control, continuously test the collected evidence against the control's predicate.
- **Status classification** — each control is in one of: `compliant`, `non_compliant`, `at_risk` (trending), `insufficient_evidence`.
- **Drift detection** — changes in control status over time, computed from evidence deltas.
- **Automated mitigation hooks** — for controls with executable mitigations, CAE can trigger them (subject to the action's own policy evaluation, RFC-0075).

Assessment results are themselves evidence, signed and appended to the Evidence Lake.

### 5. Assurance Packager

Produces the human- and machine-readable assurance artifacts:

- **Continuous Assurance Report** — control-by-control status with evidence references.
- **Assurance Snapshot** — a signed point-in-time package: all evidence, Merkle proofs, framework mapping version, assessment results. Usable as a deterministic export for auditors.
- **Assurance State** — a compact, hash-chained summary (one hash per control set) that allows a verifier to confirm "nothing changed since last attestation" with a single hash comparison.

### 6. Continuous Attestation API

The public interface through which auditors, regulators, and internal stakeholders verify assurance:

| Endpoint | Purpose |
|----------|---------|
| `assurance://cae/state` | Current Assurance State (hash-chained) |
| `assurance://cae/controls/<id>` | Live status of a single control |
| `assurance://cae/snapshot?since=` | Signed snapshot export for a time range |
| `assurance://cae/verify?proof=` | Verify a Merkle proof / attestation hash |
| `assurance://cae/report` | Generated Continuous Assurance Report |

Verification is **stateless**: a third party can verify a snapshot without trusting the CAE, using only the node's public key and the Merkle proofs.

### 7. Regulatory Mapping Doctrine

The CAE does not create a new compliance regime. It makes **existing** regimes continuously verifiable:

- **DORA (EU)** — CAE maps to ICT risk management, incident reporting (Art. 17–23), digital operational resilience testing (TLPT), and third-party risk.
- **MiCA (EU)** — CAE continuously proves reserve assets (Art. 36–39) with daily-resolved evidence rather than monthly attestations.
- **EU AI Act** — CAE maps to risk management (Art. 9), post-market monitoring (Art. 72), and incident reporting for high-risk AI systems.
- **ISO 42001** — CAE maps to the AI management system controls; the Assurance Packager emits ISO-aligned evidence sets.
- **NIS2 / ISO 27001** — CAE maps to security controls and incident evidence.

The mapping is always **bi-directionally traceable**: from a control requirement to the evidence, and from any evidence to the controls it serves.

## Conformance

A node conforms to RFC-0076 when:

1. It maintains an immutable, Merkle-ordered Evidence Lake for all governed actions.
2. It can map evidence to at least one declared control catalog.
3. It continuously assesses controls and classifies their status.
4. It can produce signed assurance snapshots verifiable without trusting the node.
5. It exposes the Continuous Attestation API.
6. It can consume RFC-0075 conflict evidence as assurance-relevant events.

## References

- RFC-0075 — Policy Conflict Resolution
- RFC-0077 — OASA Specialized Audit Profiles (defines the control catalogs for finance, stablecoins, CBDC, AI-FIN)
