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

### v0.6.0 — Interoperability
| Status | Feature | Description |
|---|---|---|
| 🚧 | Conformance Runner | Hardened, external conformance test execution |
| 📅 | External Verifier | Independent verification of evidence packages |
| 📅 | Versioned Profile | Stable Core 0.1 profile with deterministic vectors |
| 📅 | Negative Testing | Security and attack vectors added to conformance suite |

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
