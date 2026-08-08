# OASA Standards Foundation — Governance Overview

**Document type:** Operating governance summary  
**Version:** 2026-08  
**Normative reference:** [RFC-0078 OASA Standards Foundation Governance](../rfcs/RFC-0078-oasa-standards-foundation-governance.md)

This document is the operational companion to RFC-0078. It describes how the Foundation operates day-to-day: membership, decision-making, certification, and finances.

---

## 1. Mission

The OASA Standards Foundation exists to make **"OASA Certified" a trustworthy, regulator-usable mark** for autonomous systems. It achieves this by owning the OASA standard neutrally, running an independent certification program, and evolving the specification through a transparent multi-stakeholder process.

The Foundation is non-stock and vendor-neutral by structure. Kubenew is a founding contributor and reference implementer — not the owner.

---

## 2. Legal Form

- Non-stock membership corporation.
- No equity, no dividends, no sale of the standard.
- Surplus reinvested in conformance tooling, certification grants, and academic programs.

---

## 3. Membership

| Tier | Fee | Who | What you get |
|------|-----|-----|--------------|
| **Platinum** | €150,000/yr | Central banks, large institutions, major exchanges | Board seat, Standards Council seats, certification discount |
| **Gold** | €50,000/yr | Mid/large enterprises, regulated institutions | Standards Council seats, certification discount |
| **Silver** | €15,000/yr | Companies, startups, consultancies | Working-group participation, certification access |
| **Academic** | €0 | Universities, research institutions | Working-group participation, research access |
| **Individual** | €0 | Researchers, auditors, developers | Public lists, contribution via CLA |

Annual renewable. Fees fund conformance test development, certification infrastructure, and neutral operations.

---

## 4. Governance Bodies

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

- **Board of Directors** — strategy and finance. Non-vendor majority by design.
- **Standards Council** — technical governance; approves RFC progression and Standard status.
- **Working Groups** — Finance (OASA-FIN), Stablecoin, CBDC, AI-FIN, Conformance, Security & Threat Model; others created by the Council.

---

## 5. Standards Process

1. **Draft** — any member submits a Draft RFC.
2. **Working Group** — developed in the relevant WG.
3. **Community Review** — minimum 30 days public review.
4. **Reference Implementation** — required.
5. **Interop Validation** — **at least two independent, interoperable implementations** (never two from one vendor).
6. **Council Vote** — supermajority.
7. **Ratification** — frozen as an OASA Standard for the released version.

Step 5 is the structural anti-monopoly guarantee: no company becomes "the standard" by implementing it alone.

---

## 6. Certification Program

- Certification is performed by **independent certification bodies accredited by the Foundation** — never by the implementer.
- Conformance suites are public, vendor-neutral, and developed by the Conformance WG.
- Certified versions are published on a public registry (version, test results, certificate hash).
- Levels: L1 Interoperable → L2 Governed & Provenant → L3 Autonomous Execution → L4 High-Assurance + Overrides → L5 Critical Infrastructure.

---

## 7. Intellectual Property

- **Specifications:** royalty-free (Apache-2.0 text, RAND patent terms).
- **Reference implementation:** Apache-2.0.
- **Contributions:** CLA required; contributors retain copyright, grant the Foundation publication and evolution rights.
- **Patents:** RAND licensing of essential patents.

---

## 8. Finances

**Income:** membership fees, certification fees (per audit), conformance tooling licenses, research grants.

**Expenditure priorities:** conformance test suites, independent certification infrastructure, reference tooling, academic access (free).

---

## 9. Founding Recruitment Priorities

To reach critical mass in the first two years:

1. **2–3 large regulated institutions** (Gold/Platinum) — anchor the finance domain and OASA-FIN.
2. **1 central bank pilot** — anchor OASA-CBDC and give regulator-facing legitimacy.
3. **1–2 stablecoin issuers** — anchor OASA-STABLE with the monthly→continuous attestation upgrade story.
4. **Academic partners** (free tier) — keep the research pipeline open and the standard credible.

---

## 10. Decision Checklist for Prospective Members

- Is the standard governed by a body I do not control? (Yes — non-vendor board majority.)
- Can my competitors implement it too? (Yes — required: two independent implementations.)
- Is it open source? (Apache-2.0 reference implementation.)
- Does it map to regulation I already owe? (DORA, MiCA, EU AI Act, ISO 27001/42001, SOC 2.)
- Can it be trusted by a regulator? (Independent certification bodies, public registry, statelessly verifiable attestation.)
