# OASA Foundation: GitHub Organization Layout

**Status:** Canonical Structure  
**Reference:** OASA Foundation Charter (Article II: 4-Quadrant Governance)

To enforce the vendor-neutral, anti-capture governance model defined in the Foundation Charter, the GitHub organization (`github.com/oasa-foundation`) must be structurally partitioned. Access, code ownership, and merge privileges are distributed according to the 4-Quadrant voting structure.

---

## 1. Core Cryptographic & Protocol Repositories

These repositories contain the unamendable core protocol, TPM attestation logic, and WORM ledger implementations. 

**Access Policy:** Merges require cryptographically signed approval from at least two (2) members of the **Technical Maintainer Quadrant**. 

- `oasa-foundation/ss-kernel`: The core Rust execution services, including the eBPF capability tracing engine.
- `oasa-foundation/ss-crypto`: The cryptographic primitives, Ed25519 identity generation, and signature verification implementations.
- `oasa-foundation/oasa-manifests`: The centralized repository for all signed releases, utilizing the 5-of-9 threshold release keys.

## 2. Conformance & Validation Repositories

These repositories define the testing vectors, stress-test harnesses, and certification profiles. They are the primary domain of the **Contester & Auditor Quadrant**.

**Access Policy:** The Contester Class holds an asymmetric veto over any PR that reduces test strictness or modifies failure semantics (Exit Codes 1, 2, 3).

- `oasa-foundation/conformance-suite`: The deterministic test vectors (e.g., `identity-creation`, `capability-grant`) and python execution harnesses.
- `oasa-foundation/stress-test-harness`: Adversarial testing frameworks, including the Class I/II/III deviation injector (`run-stress-test`).

## 3. Governance & Pedagogy Repositories

These repositories hold the constitutional documents, RFCs, and academic resources. They are jointly managed by the **Academic Core** and **Technical Maintainer** Quadrants.

- `oasa-foundation/governance`: The OASA Foundation Charter, RFC process tracking, and board election records.
- `oasa-foundation/case-studies`: University-level pedagogical material, including the canonical *Case of the Unauthorized Agent*.
- `oasa-foundation/rfcs`: The technical Request For Comments (RFC) specifications.

## 4. Platform Adapters & Reference Integrations

These repositories contain the thin translation layers that map third-party infrastructure (like HPE Morpheus) into the SovereignStack evidence format. They are heavily influenced by the **Enterprise Operator Quadrant**.

**Access Policy:** Enterprise operators may maintain their specific adapters, but cannot alter the core provenance logic.

- `oasa-foundation/adapter-morpheus`: The reference integration for HPE Morpheus VM Essentials.
- `oasa-foundation/adapter-kubernetes`: Standardized Kubernetes CRD event ingestion adapters.

---

## Access Control Matrix (CODEOWNERS)

The `.github/CODEOWNERS` file across all repositories must reflect this structural separation:

```text
# General Core Maintenance
* @oasa-foundation/tech-maintainers

# Conformance Strictness (Contester Veto Enforcement)
/conformance/vectors/ @oasa-foundation/contester-auditors
/tools/ss-test @oasa-foundation/contester-auditors

# Governance & Pedagogy
/docs/case-studies/ @oasa-foundation/academic-core
CONSTITUTION.md @oasa-foundation/board-of-directors
```
