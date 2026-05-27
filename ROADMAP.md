# SovereignStack Roadmap

**Updated:** May 2026  
**Tracking:** [GitHub Projects](https://github.com/Kubenew/SovereignStack/projects)

---

## 2026.1 — Foundation (Current)

| Status | Feature | Description |
|---|---|---|
| ✅ | OASA Specification | Protocol axioms, compliance lock, audit schema |
| ✅ | Helm Chart | Full Kubernetes deployment with NetworkPolicies, gVisor |
| ✅ | vLLM Integration | PagedAttention, AWQ/FP8, Tensor Parallel, OpenAI API |
| ✅ | Dynamic VRAM Scaling | Automatic context window from hardware budget |
| ✅ | OPA Policy Engine | DLP, prompt injection, RBAC via sidecar |
| ✅ | CI/CD Matrix | Multi-Python (3.10–3.12), conformance L1/L2/L3 |
| ✅ | Keycloak OIDC | Auto-imported realm, RBAC, token validation |
| ✅ | Threat Model | STRIDE catalogue, 8 trust zones, compliance mapping |
| ✅ | Observability | OpenTelemetry traces, Prometheus metrics |

## 2026.2 — Standards & Governance (Next)

| Status | Feature | Description |
|---|---|---|
| 🚧 | RFC Process | Standards evolution workflow |
| 🚧 | Architecture Docs | System topology, layer model, subsystem boundaries |
| 🚧 | Deployment Profiles | Edge, Air-Gap, Datacenter, Personal |
| 🚧 | Reproducible Builds | Nix/Guix, signed releases, SBOM in CI |
| 🚧 | Governance Model | Maintainer roles, working groups, decision process |

## 2026.3 — Federation & Memory

| Status | Feature | Description |
|---|---|---|
| 📅 | OASA Merkle-Tree Auditing | Append-only cryptographically verified log chains |
| 📅 | Federated Memory | CRDT-based cross-node vector sync |
| 📅 | Mesh Networking | WireGuard-based inter-node routing |
| 📅 | Secure Weight Federation | Sharded cross-node inference without sharing weights |

## 2027.1 — Enterprise Hardening

| Status | Feature | Description |
|---|---|---|
| 📅 | Hardware Enclave Ingest | SGX/SEV-SNP confidential computing |
| 📅 | SBOM & Cosign Signing | Supply chain security for all artifacts |
| 📅 | SPIFFE/SPIRE Identity | Workload identity for zero-trust mesh |
| 📅 | Sovereign Node OS | Immutable OS image (NixOS/Talos-based) |

## 2027.2 — Agent Orchestration

| Status | Feature | Description |
|---|---|---|
| 📅 | Agent Runtime | Lifecycle management, scheduling, memory attachment |
| 📅 | Multi-Model Orchestration | Routing, fallback, ensemble inference |
| 📅 | Federated Agents | Cross-node agent coordination |
| 📅 | Marketplace | Agent modules, deployment bundles, plugins |

## 2027.3+ — Autonomous Infrastructure

| Status | Feature | Description |
|---|---|---|
| 🔮 | Sovereign Mesh Federation | Regional mesh → federated AI clusters |
| 🔮 | Autonomous Operations | Self-healing, auto-scaling, predictive scheduling |
| 🔮 | Certification Program | Certified Node, Runtime, Federation |
| 🔮 | Enterprise Platform | Support contracts, managed updates, deployment audits |

---

## Legend

| Mark | Meaning |
|---|---|
| ✅ | Shipped |
| 🚧 | In progress |
| 📅 | Planned |
| 🔮 | Future concept |
