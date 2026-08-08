# RFC-0078: OASA Standards Foundation Governance

**Status:** Draft | **Type:** Process | **Created:** 2026-08-07 | **Depends On:** RFC-0010  
**Related:** [GOVERNANCE](../GOVERNANCE.md), [CONSTITUTION](../CONSTITUTION.md), [STANDARDS](../STANDARDS.md)

## Abstract

Defines the governance structure of the **OASA Standards Foundation** — the multi-stakeholder body that owns the OASA standard, certifies conformant implementations, and evolves the specification. The Foundation is deliberately **vendor-neutral**: OASA is not owned by a single company. Kubenew is a founding contributor and reference implementer, not the owner.

The Foundation's purpose is to make "OASA Certified" a trustworthy, regulator-usable mark — which requires that the standard, the certification, and the certification process be governed independently and transparently.

## Motivation

Standards succeed when they are trusted. A certification mark controlled by the vendor whose product carries it has no regulatory weight. For OASA to serve DORA, MiCA, and EU AI Act compliance, the standard must be:

- **Neutral** — not capturable by any single vendor.
- **Transparent** — the standard, its process, and its decisions are public.
- **Verifiable** — certification is reproducible by independent auditors.
- **Aligned** — mapping to existing regulation, not competing with it.

This RFC is the process document that makes these properties structurally guaranteed rather than aspirational.

## Specification

### 1. Legal Form

The OASA Standards Foundation is a **non-stock membership corporation**, modeled on the governance patterns of the IETF, Linux Foundation, and OpenHarmony.

- No equity, no dividends, no sale of the standard.
- Assets are the standard, the certification program, and the reference tooling.
- Surplus funds are reinvested in conformance tooling, certification grants, and academic programs.

### 2. Membership Tiers

| Tier | Fee | Eligibility | Rights |
|------|-----|-------------|--------|
| **Platinum** | €150,000/yr | Large institutions, central banks, major exchanges | Board seat, standards committee seats, certification discount |
| **Gold** | €50,000/yr | Mid/large enterprises, regulated institutions | Standards committee seats, certification discount |
| **Silver** | €15,000/yr | Companies, startups, consultancies | Working-group participation, certification access |
| **Academic** | €0 | Universities, research institutions | Working-group participation, research access |
| **Individual** | €0 | Researchers, auditors, developers | Public mailing lists, contribution via CLA |

Membership is annual and renewable. Fees fund the certification program, conformance test development, and neutral infrastructure.

### 3. Governance Bodies

```
┌─────────────────────────────┐
│        Board of Directors   │  ← elected by Platinum + Gold
│  (vendor-neutral majority)  │
└─────────────┬───────────────┘
              │
   ┌──────────┴──────────┐
   │  Standards Council  │  ← sets RFC process, approves Standards
   └──────────┬──────────┘
              │
   ┌──────────┴───────────┐
   │  Working Groups      │  ← profiles, conformance, security, domain
   └──────────────────────┘
```

- **Board of Directors** — strategic and financial governance. A majority of board seats are reserved for non-vendor members (Platinum/Gold institutions and independent experts) to prevent vendor capture.
- **Standards Council** — technical governance. Approves RFC progression and "OASA Standard" status. Members are technical delegates, including at least one from Kubenew as reference implementer.
- **Working Groups** — domain-specific: Finance (OASA-FIN), Stablecoin, CBDC, AI-FIN, Conformance, Security & Threat Model, and others created by the Council.

### 4. Standards Process (IETF-style)

1. **Draft** — any member submits a Draft RFC.
2. **Working Group** — assigned to the relevant WG for development.
3. **Community Review** — public review period (minimum 30 days).
4. **Reference Implementation** — required: a working implementation of the proposal.
5. **Interop Validation** — required: **at least two independent, interoperable implementations** (not both from one vendor) must demonstrate interoperation.
6. **Council Vote** — the Standards Council votes; a supermajority is required.
7. **Ratification** — the RFC becomes an **OASA Standard** and is frozen for the released version.

Point 5 is the structural anti-monopoly guarantee: no company can become "the standard" by implementing it alone.

### 5. Certification Program

- **Certification** is performed by **independent certification bodies** accredited by the Foundation — never by the implementer itself.
- **Conformance test suites** are developed by the Conformance WG and are public and vendor-neutral.
- **Certified versions** are listed on a public registry with the exact version, test results, and certificate hash.
- Certification maps to levels (see [CERTIFICATION](../CERTIFICATION.md)): L1 Interoperable → L5 Critical Infrastructure.

### 6. Intellectual Property Policy

- **Specifications:** published under a royalty-free license (Apache-2.0 text, RAND patent terms).
- **Reference implementation:** Apache-2.0.
- **Contributions:** governed by a Contributor License Agreement (CLA) granting the Foundation the rights needed to publish and evolve the standard while contributors retain copyright.
- **Patent commitment:** participants agree to RAND (Reasonable And Non-Discriminatory) licensing of essential patents.

### 7. Funding & Sustainability

Income sources:

1. Membership fees.
2. Certification fees (per-audit, paid by the certified institution).
3. Conformance tooling licenses (for commercial users).
4. Grants and research sponsorship (central banks, academic programs).

Expenditure priorities:

1. Conformance test suite development.
2. Independent certification infrastructure.
3. Reference tooling.
4. Accessibility: no-fee academic membership keeps research open.

## Conformance

A governance body conforms to RFC-0078 when:

1. It is legally non-stock and vendor-neutral by structure.
2. Its board has a non-vendor majority.
3. Its standards process requires two independent implementations for "Standard" status.
4. Certification is performed by accredited independent bodies.
5. Specifications and reference implementations are published under royalty-free licenses.

## References

- RFC-0010 — Conformance Framework (levels and test methodology)
- RFC-0076 — OASA Continuous Assurance Engine (subject of certification)
- RFC-0077 — OASA Specialized Audit Profiles
- [GOVERNANCE](../GOVERNANCE.md) — project-level governance (this RFC governs the Foundation; GOVERNANCE.md governs the repository)
