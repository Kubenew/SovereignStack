# OASA Strategic Positioning

**Document type:** Board-ready strategy  
**Version:** 2026-08  
**Related:** [RFC-0075 Policy Conflict Resolution](../rfcs/RFC-0075-policy-conflict-resolution.md), [RFC-0076 CAE](../rfcs/RFC-0076-oasa-continuous-assurance-engine.md), [RFC-0077 Audit Profiles](../rfcs/RFC-0077-oasa-specialized-audit-profiles.md), [RFC-0078 Foundation Governance](../rfcs/RFC-0078-oasa-standards-foundation-governance.md)

---

## 1. Positioning Statement

**SovereignStack / OASA is the operating system for verifiable regulatory compliance in autonomous digital economies.**

For CTOs, CISOs, and Heads of Compliance at regulated financial institutions, OASA is the open standard and infrastructure that lets autonomous AI systems act — and **proves** — continuously, that every action was governed, authorized, and law-compliant.

OASA is not "an AI framework." It is **Open Verification and Governance Infrastructure** — the cryptographic and governance layer that makes autonomous systems auditable the way regulated institutions already are, and regulators already expect.

---

## 2. The Problem

Autonomous agents are being asked to execute high-stakes financial actions:

- Treasury agents moving value
- Compliance agents routing cross-border payments
- Trading agents executing under MiCA and MiFID II
- Reserve management for stablecoin issuers

But the market cannot yet say, with evidence, that an autonomous system is compliant. Today's reality:

- **Point-in-time certification** — audited once a year, drifting the rest of the year.
- **Black-box decisions** — an AI makes a call; nobody can prove why.
- **No audit trail** — "the model did it" is not evidence.
- **Conflicting rules** — organizational, jurisdictional, and regulatory policies collide, and the collision is resolved by whoever wrote the code first.

Regulators are waking up to this: DORA, MiCA, EU AI Act, NIS2, ISO 42001 all demand ongoing, verifiable oversight of automated systems. The demand for "prove it" is about to become law everywhere.

---

## 3. The OASA Answer

OASA turns "prove it" from an annual ritual into a continuous, machine-verifiable property:

| Legacy Approach | OASA Approach |
|-----------------|---------------|
| Audit once a year | Continuous assurance, attested every instant |
| Manual evidence collection | Evidence lake: every governed action is signed, Merkle-chained evidence |
| Policy conflicts resolved by luck | Deterministic conflict-resolution hierarchy; unresolved conflicts **halt and escalate to a human** |
| PDF audit report | Statelessly verifiable assurance snapshots (hash + Merkle proof) |
| "The model did it" | Every decision traces to signed policy, capability, model lineage, and evidence |

The three RFCs that make this concrete:

1. **RFC-0075 — Policy Conflict Resolution.** When organizational, jurisdictional, and regulatory policies collide, resolution is deterministic and auditable — and when it cannot be resolved, the system safely halts and escalates. No guessing.
2. **RFC-0076 — Continuous Assurance Engine (CAE).** A tamper-evident evidence lake continuously mapped to control frameworks (DORA, MiCA, EU AI Act, ISO 27001/42001, SOC 2), producing verifiable assurance state.
3. **RFC-0077 — Specialized Audit Profiles.** Pre-built control catalogs for finance (OASA-FIN), stablecoins (OASA-STABLE), CBDC (OASA-CBDC), and AI-finance (OASA-AI-FIN) — mapping existing law, not inventing new compliance.

---

## 4. Target Market & Buyer

**Primary buyers:** CTOs, CISOs, Heads of Compliance at:

- Regulated financial institutions and payment processors
- Stablecoin issuers and exchanges
- Central banks and wholesale settlement operators
- Financial AI/agent product teams

**The pitch in one sentence:** *"You already have to comply with DORA/MiCA/ISO 42001. OASA is the infrastructure that proves you comply — continuously, cryptographically, and auditably — so your AI can act."*

---

## 5. Go-to-Market

### Phase 0 — Reference & Proof (now)
- Public, Apache-2.0 SovereignStack with conformance suite (L1–L4)
- Finance Reference Node with 30+ passing assertions, demo-ready
- RFC-0075/76/77/78 published as drafts
- Foundation governance model published (RFC-0078)

### Phase 1 — Foundation & Community
- Stand up the OASA Standards Foundation (RFC-0078)
- Recruit founding members: 2–3 large institutions + 1 central bank pilot
- Publish conformance suites and first OASA Certified implementations

### Phase 2 — Continuous Assurance Product
- CAE as a product: Professional (on-prem) and Enterprise (multi-node federation)
- Certification program with accredited independent certifiers
- OASA-FIN / OASA-STABLE / OASA-CBDC / OASA-AI-FIN as sold profiles

### Phase 3 — Regulator Engagement
- Map CAE outputs to DORA/TLPT, MiCA reserve evidence, EU AI Act post-market monitoring
- Liaison with regulators to accept continuous attestation as audit evidence
- Position OASA Certified as the recognized mark for autonomous compliance

---

## 6. Business Model

- **Open core:** protocol, gateway, and reference implementation are free (Apache-2.0)
- **Revenue:**
  - CAE Professional / Enterprise subscriptions
  - Certification fees (per audit, paid by the certified institution)
  - Conformance tooling for commercial users
  - Auditors' training and accreditation programs
- **Foundation funding:** Platinum (€150k), Gold (€50k), Silver (€15k), Academic (€0) — see RFC-0078

---

## 7. Why OASA Wins

1. **First-mover in verifiable autonomous compliance.** Nobody else is shipping cryptographic, continuous, regulator-mapped assurance for AI agents.
2. **Map to existing law, not new law.** Institutions don't adopt a new regime; they get continuous proof for regimes they already owe.
3. **Safe by construction.** Safe-halt conflict resolution means the system is auditable *and* conservative — regulators' and CISOs' favorite combination.
4. **Vendor-neutral by structure.** The Foundation's two-independent-implementations rule means no single vendor can capture the standard.
5. **Open + enterprise-ready.** Public standard, reference implementation, and a commercial CAE layer.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Regulators don't accept continuous attestation | Phase 3 regulator liaison; map 1:1 to DORA/TLPT, MiCA, EU AI Act |
| Standards-body competition (ISO AI standards) | OASA is an implementation of ISO/regulatory intent, not a competing regime |
| Institutions skeptical of AI autonomy | Safe-halt default + human override means OASA is more conservative than manual operations |
| Vendor capture | Foundation structure: non-vendor board majority + two-implementation rule |
| Adoption inertia | Free open core, public conformance suite, academia access at zero cost |

---

## 9. The Board Summary

> Autonomous systems will run regulated finance. They will do it either **blind** — ungoverned, unauditable, and at regulatory risk — or **governed** — with continuous, cryptographic proof of compliance. OASA is the open infrastructure that makes governed autonomy possible. It maps to the regulations institutions already owe, it is safe by construction, and it is governed neutrally so it can be trusted. We are building it now, and it is ready to present to a board, a regulator, or a potential founding member of the OASA Standards Foundation.
