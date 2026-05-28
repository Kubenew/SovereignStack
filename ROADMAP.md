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

## 2026.2 — Standards & Governance

| Status | Feature | Description |
|---|---|---|
| ✅ | RFC Process | Standards evolution workflow (RFC 0000–0006) |
| ✅ | Architecture Docs | System topology, layer model, subsystem boundaries |
| ✅ | Deployment Profiles | Edge, Air-Gap, Datacenter, Personal + edge guide |
| ✅ | Reproducible Builds | Hash-pinned deps, digest-pinned images, SBOM + cosign in CI |
| ✅ | Governance Model | Maintainer roles, working groups, lazy consensus |
| ✅ | Agent Orchestration | Agent API (RFC 0005), lifecycle, scheduling, tool plugins |

## 2026.3 — Federation & Memory

| Status | Feature | Description |
|---|---|---|
| ✅ | Node Identity | Ed25519 keys, TPM AIK, X.509 cert chain (RFC 0003) |
| ✅ | Federation Protocol | WireGuard mesh, CRDT sync, jurisdictional gating (RFC 0004) |
| ✅ | Memory Spec | Vector store, KV cache, event log, CRDT sync (RFC 0006) |
| ✅ | OASA Merkle-Tree Auditing | Append-only cryptographically verified log chains |
| 📅 | Secure Weight Federation | Sharded cross-node inference without sharing weights |

## 2027.1 — Enterprise Hardening

| Status | Feature | Description |
|---|---|---|
| ✅ | SBOM & Cosign Signing | Syft SPDX+CycloneDX, cosign verification in CI |
| ✅ | SPIFFE/SPIRE Identity | Workload identity, SVID fetch, audit attribution |
| ✅ | Prometheus Alerting | 21 alerts across 6 rule groups |
| ✅ | Edge Deployment Guide | K3s + ARM + Longhorn reference |
| ✅ | Hardware Enclave Ingest | SGX/SEV-SNP confidential computing |
| ✅ | Sovereign Node OS | Immutable OS image (NixOS/Talos-based) |

## 2027.2 — Agent Ecosystem

| Status | Feature | Description |
|---|---|---|
| ✅ | Agent Runtime (RFC) | Agent manifest, 8 endpoints, SSE streaming, memory attachment |
| ✅ | Compliance Framework | GDPR, HIPAA, SOC 2 control mapping |
| ✅ | Security Overview | Defense-in-depth across 3 identity layers |
| ✅ | Multi-Model Orchestration | Routing, fallback, ensemble inference |
| ✅ | Federated Agents | Cross-node agent coordination |
| ✅ | Marketplace | Agent modules, deployment bundles, plugins |

## 2027.3+ — Autonomous Infrastructure

| Status | Feature | Description |
|---|---|---|
| ✅ | Sovereign Mesh Federation | Regional mesh → federated AI clusters |
| ✅ | Autonomous Operations | Self-healing, auto-scaling, predictive scheduling |
| 📅 | Certification Program | Certified Node, Runtime, Federation |
| 📅 | Enterprise Platform | Support contracts, managed updates, deployment audits |

## 2026 Kubernetes Enhancements

| Status | Feature | Description |
|---|---|---|
| ✅ | Canonical CRD | Native `sovereignstack.yaml` Kubernetes CRD management |
| ✅ | High Availability | PodDisruptionBudget for safe evictions |
| ✅ | Canary Rollouts | RollingUpdate configurations for inference endpoints |

---

## Legend

| Mark | Meaning |
|---|---|
| ✅ | Shipped |
| 🚧 | In progress |
| 📅 | Planned |
| 🔮 | Future concept |
