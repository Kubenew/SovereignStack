# RFC-0077: OASA Specialized Audit Profiles

**Status:** Draft | **Type:** Standard | **Created:** 2026-08-07 | **Depends On:** RFC-0075, RFC-0076  
**Related:** [CERTIFICATION](../CERTIFICATION.md), [OASA](../OASA.md)

## Abstract

Defines **OASA Specialized Audit Profiles** — pre-built control catalogs and evidence mappings that make the OASA Continuous Assurance Engine (RFC-0076) directly deployable for specific regulated domains. Each profile maps existing law and regulation onto OASA evidence, so institutions receive **continuous assurance for the frameworks they are already governed by** — no new compliance regime is invented.

The initial profiles are:

| Profile | Domain | Anchor Regulation |
|---------|--------|-------------------|
| **OASA-FIN** | General finance / payments | MiFID II, PSD2, DORA |
| **OASA-STABLE** | Stablecoin issuers & reserve management | MiCA (Reserve & Redemption, Art. 36–46) |
| **OASA-CBDC** | Central bank digital currency operations | Central bank mandates, settlement finality |
| **OASA-AI-FIN** | AI-driven financial decisioning | EU AI Act, ISO 42001 |

## Motivation

A generic "continuous assurance" capability is not directly actionable: a stablecoin issuer, a payment processor, and a central bank are governed by different rules and need different evidence. Specialized Audit Profiles close that gap by turning each regulatory regime into a **machine-checkable control catalog** plus the evidence mappings the CAE needs to evaluate it continuously.

Profiles also carry the commercial strategy: OASA does not sell "an AI framework." It sells **proof** — proof that maps 1:1 to the regulations the institution is already obligated to meet.

## Specification

### 1. Profile Structure

Every profile is composed of:

- **Control Catalog** — the regulatory requirements, expressed as versioned, machine-checkable controls (Section 3 of RFC-0076).
- **Evidence Mapping** — which OASA evidence types satisfy which controls.
- **Assessment Cadence** — how often each control must be evaluated (daily, continuous, event-triggered).
- **Anchoring** — the regulatory text each control derives from, with citations.
- **Reporting Kit** — the out-of-the-box report/attestation formats for that regulator.

A profile MUST be versioned, and a mapping change MUST be an auditable event (per RFC-0076 §3).

### 2. OASA-FIN — General Finance & Payments

**Anchor:** MiFID II, PSD2, DORA

Key controls:

- **Transactional authorization** — every payment/execution is policy-authorized (RFC-0075) and evidence-recorded.
- **Record integrity** — all records content-addressed and Merkle-protected; tampering detection within one block.
- **Incident detection & response** — DORA Art. 17–23: ICT incidents detected, classified, and reported within mandated windows (evidence cadence: continuous).
- **Third-party oversight** — all delegated capabilities (RFC-0026) are mapped and risk-rated.
- **Conflict evidence** — every policy conflict and its resolution is evidence (RFC-0075), supporting auditability of autonomous execution.

### 3. OASA-STABLE — Stablecoin Issuance & Reserve Management

**Anchor:** MiCA (Title IV — Asset-Referenced Tokens; Title III — E-Money Tokens)

Key controls:

- **Reserve sufficiency** — continuous proof that reserve assets cover outstanding tokens (MiCA Art. 36–39). Where legacy compliance is monthly, OASA provides **daily-resolved, continuously attested** evidence.
- **Reserve segregation** — evidence that reserves are held in custody separate from issuer operations.
- **Redemption right** — proof that redemption requests are honored on legal-tender value within mandated periods (MiCA Art. 46).
- **Conflict resolution** — proof that redemption/payment conflicts are resolved per RFC-0075 hierarchy, not ad hoc.
- **Custody integrity** — signed evidence of asset movement, custody location, and valuation.

Commercial note: monthly attestation → continuous attestation is the single most persuasive upgrade story for stablecoin issuers.

### 4. OASA-CBDC — Central Bank Digital Currency

**Anchor:** Central bank mandates; settlement finality; monetary law

Key controls:

- **Tiered governance** — the central bank retains hierarchical control; delegated capabilities are constrained and revocable (RFC-0026).
- **Settlement finality** — evidence that settlement is atomic, final, and irreversible per the mandate.
- **Monetary integrity** — issuance and redemption flows are policy-authorized with constitutional hard-supremacy (RFC-0075 §4.1).
- **Offline & resilience** — evidence of availability and resilience per the bank's continuity profile.
- **Wholesale/retail split** — separate control catalogs for wholesale settlement rails and retail digital cash.

### 5. OASA-AI-FIN — AI-Driven Financial Decisioning

**Anchor:** EU AI Act, ISO 42001, DORA

Key controls:

- **Risk management** — high-risk AI decisioning has a risk-management system (EU AI Act Art. 9) evidenced continuously.
- **Agent Authorization Boundary** — every autonomous financial decision is bounded by an explicit, evidence-recorded authorization envelope; actions outside the boundary halt (RFC-0075 safe-halt).
- **Post-market monitoring** — drift and behavior change are detected and logged (EU AI Act Art. 72).
- **Model lineage** — every decision traces to a signed model version (RFC-0040 model lineage).
- **Incident reporting** — serious incidents reported within statutory windows, backed by evidence.

### 6. Profile Adoption Workflow

1. **Select profile(s)** matching the institution's regulated activity.
2. **Import catalog** into the CAE Framework Mapper.
3. **Map existing policies** to controls; any unmapped obligation becomes a gap.
4. **Run continuous assessment** and produce the first Continuous Assurance Snapshot.
5. **Attest** — export signed snapshot for auditor/regulator.

## Conformance

A profile conforms to RFC-0077 when:

1. Every control is traceable to a cited regulatory source.
2. Every control maps to at least one OASA evidence type.
3. Assessment cadence is explicit.
4. The profile is versioned and its changelog is auditable.
5. The profile works with an RFC-0076-compliant CAE without bespoke integration.

## References

- RFC-0075 — Policy Conflict Resolution (governs autonomous authorization)
- RFC-0076 — OASA Continuous Assurance Engine (executes the profiles)
- RFC-0040 — Model Lineage Protocol (OASA-AI-FIN)
- RFC-0026 — Capability Delegation (OASA-CBDC tiered governance)
