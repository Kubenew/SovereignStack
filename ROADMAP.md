# SovereignStack Roadmap

**Updated:** July 2026  
**Tracking:** [GitHub Projects](https://github.com/sovereignstack/sovereignstack/projects)

---

## Executable Milestones

The roadmap focuses on executable milestones and reference implementations, demonstrating the maturity of the specifications. SovereignStack is positioned as a vendor-neutral governance layer, with HPE Morpheus as its first enterprise reference environment.

*(For the historical 2026-2027+ roadmap, see [docs/history/ROADMAP-2026.md](docs/history/ROADMAP-2026.md))*

### v0.5.0 — Core Contract (Stabilization)
| Status | Feature | Description |
|---|---|---|
| ✅ | Identity & Capability | Ed25519 identity generation and capability management |
| ✅ | Policy & Events | Policy rule matching and event integrity |
| ✅ | Provenance Engine | Cryptographic event log and tamper-evident chains |
| ✅ | Evidence | Independently verifiable evidence generation |
| ✅ | Core Conformance | Deterministic test vectors and claims mapping |

### v0.6.0 — Governed Autonomous Action (Flagship Milestone)
> **SovereignStack v0.6 introduces Governed Autonomous Action: a vendor-neutral protocol for authorizing, executing, recording and independently verifying AI-driven infrastructure operations.**

**The Golden Path:** `DISCOVER → AUTHORIZE → EXECUTE → RECORD → VERIFY`  
**Execution Order:** OASA Core contract → minimal Core → conformance → Morpheus reference adapter → 3-minute demo → ecosystem outreach

| Status | Feature | Description |
|---|---|---|
| 🚧 | OASA Core Contract | 5 API verbs (`/discover`, `/authorize`, `/execute`, `/record`, `/verify`), vendor-neutral `target://scheme` dispatch |
| 📅 | Minimal Core Engine | Server-side atomic single-use tokens, canonical JSON signing, configured cryptographic keys |
| 📅 | Normative Conformance | 16 essential tests (anti-theater denial, verifiable evidence golden path, atomic consumption, tampering detection, provider evidence) |
| 📅 | Morpheus Reference Adapter | First reference execution adapter (`target://morpheus`) with native provider action ID binding |
| 📅 | Flagship Demo | 3-minute end-to-end scenario: Deny Prod → Allow Staging → Morpheus Exec → Independent Verifier PASS |

### v0.7.0 — HPE Morpheus Integration
| Status | Feature | Description |
|---|---|---|
| 📅 | Morpheus Adapter | Discovery and infrastructure event ingestion |
| 📅 | Identity Mapping | Map Morpheus workloads to SovereignStack identity |
| 📅 | Capability Enforcement | Map Morpheus RBAC/roles to SovereignStack capabilities |
| 📅 | Policy Gates | Pre-flight policy enforcement for Morpheus provisioning |
| 📅 | Provenance Export | Cryptographic evidence of Morpheus infrastructure changes |

### v0.8.0 — OASA Assurance
| Status | Feature | Description |
|---|---|---|
| 🔮 | OASA Assurance Profile | Map cryptographic evidence to relevant OASA controls |
| 🔮 | Automated Assessment | Produce machine-verifiable compliance reports |

### v0.9.0 — External Validation
| Status | Feature | Description |
|---|---|---|
| 🔮 | Independent Conformance | External organizations run the deterministic suite |
| 🔮 | Reference Implementations | Three independent implementations passing conformance |

### v1.0.0 — SovereignStack Core
| Status | Feature | Description |
|---|---|---|
| 🔮 | Stable Protocol | Immutable v1.0 core protocol specifications |
| 🔮 | Profiles Framework | Stable framework for extending core with industry profiles |
| 🔮 | Certification Program | Formal SovereignStack certification program launch |

---

## Legend

| Mark | Meaning |
|---|---|
| ✅ | Shipped |
| 🚧 | In progress |
| 📅 | Planned |
| 🔮 | Future concept |
