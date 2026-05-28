# CNCF Sandbox Application: SovereignStack

## Project Name

**SovereignStack** — Sovereign AI Infrastructure

## Project Description

SovereignStack is an open-source, cloud-native platform for running large language model (LLM) inference workloads with full data sovereignty. It provides a self-hosted, air-gapped AI stack that enforces compliance locks, jurisdictional routing, and cryptographic audit trails — enabling organizations to deploy AI infrastructure without exfiltrating data to external APIs.

The platform wraps vLLM (and other engines) behind a gateway with OIDC authentication, OPA policy enforcement, Prometheus monitoring, and pluggable memory storage. It defines the **Open Autonomous Stack Architecture (OASA)** specification — a standards-track protocol for sovereign AI nodes, mesh federation, and agent orchestration.

## Cloud Native Alignment

| Principle | Alignment |
|---|---|
| **Microservices** | Gateway, memory, ingest, vLLM, Keycloak as independent services |
| **Containerized** | Docker Compose + Helm chart, digest-pinned images |
| **Orchestration** | Kubernetes via Helm (NetworkPolicies, gVisor, resource limits) |
| **Observability** | OpenTelemetry traces, Prometheus metrics, 21 alerting rules |
| **Declarative APIs** | Kubernetes-style `kind: Agent` manifests, OASA `sovereign-stack.yaml` |
| **CI/CD** | GitHub Actions, matrix testing (py3.10-3.12), conformance levels L1/L2/L3 |
| **Supply Chain** | Hash-pinned dependencies, SBOM (Syft SPDX+CycloneDX), cosign verification |
| **Service Mesh** | SPIFFE/SPIRE workload identity, mTLS-ready, WireGuard mesh |
| **Storage** | Pluggable Qdrant/PostgreSQL/pgvector, AES-256-GCM at rest |

## Use Cases

1. **Enterprise AI Gateway** — OIDC-authenticated, policy-enforced access to local LLMs with audit trails
2. **Air-Gapped Inference** — `oasa_compliance_lock` prevents any data exfiltration to external APIs
3. **Federated Sovereign Mesh** — Multi-node CRDT-synced memory with jurisdictional gating
4. **Agent Orchestration** — Declarative agent lifecycle with memory attachment and tool plugins
5. **Edge AI** — K3s + ARM deployment guide for RPi5/Rock 5B with llama.cpp

## Existing Adoption

- Two organizations (one EU healthcare, one US defense contractor) evaluating for internal deployments
- 100+ GitHub stars, active contributor base
- Conformance suite (54 tests) used as reference by OASA implementers

## Maturity

| Area | Status |
|---|---|
| Architecture | 9-layer system topology documented in ARCHITECTURE.md |
| API | REST + SSE streaming, OpenAPI spec, conformance tests |
| Governance | GOVERNANCE.md, MAINTAINERS.md, RFC process (6 RFCs) |
| Security | 53 STRIDE threats (threat-model.md), SPIFFE integration, compliance framework (GDPR/HIPAA/SOC 2) |
| Roadmap | 2026.1–2027.3+ with status tracking |
| CI | GitHub Actions, matrix testing, SBOM, cosign, JUnit artifacts |
| License | Apache 2.0 |

## Sponsor Information

*[Sponsor name] — [Affiliation]*

## Project Logo

*[Logo URL]*

## Authors

- [Project maintainers](MAINTAINERS.md)

## Additional Resources

- **Repository:** https://github.com/Kubenew/SovereignStack
- **Documentation:** https://github.com/Kubenew/SovereignStack/tree/main/docs
- **RFCs:** https://github.com/Kubenew/SovereignStack/tree/main/rfcs
- **Conformance Tests:** https://github.com/Kubenew/SovereignStack/tree/main/tests
- **Website:** *[planned]*
