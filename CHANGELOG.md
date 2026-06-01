# Changelog

All notable changes to SovereignStack are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project uses [Calendar Versioning](https://calver.org) (`YYYY.N`).

---

## [v0.3.0] — 2026-06-15

### Added

#### Standards Ecosystem (10 new RFCs)
- **RFC-0001** — Sovereign Object Model (universal base: id, type, owner, version, provenance)
- **RFC-0002** — URI Standard with formal ABNF grammar (11 registered schemes)
- **RFC-0003** — Trust Graph (identity, verification, certification, reputation, trust objects)
- **RFC-0004** — Capability Registry (DNS + service discovery for intelligence)
- **RFC-0005** — Knowledge Objects (structured, verifiable knowledge with evidence & reasoning)
- **RFC-0006** — Reasoning Objects (immutable inference traces with step-by-step replay)
- **RFC-0007** — Event Bus (append-only Merkle-chained event store, 16 event types)
- **RFC-0008** — Federation Routing (mDNS/DNS/DHT discovery, trust negotiation, replication)
- **RFC-0009** — Session Lifecycle (Pending→Running→Suspended→Terminated state machine)
- **RFC-0010** — Conformance Framework (4 profiles, test suites, attestation format)

#### Architecture Documentation
- `docs/architecture/` — 10-page architecture breakdown with SVG diagram
- Kernel (identity, resolver, eventbus, registry, capability, policy)
- Session runtime, Identity, Memory hierarchy, Federation, Capabilities
- Governance, Trust graph, SIP protocol details

#### Reference Implementation
- `ss-kernel/` — Formal Rust crate with 6 core services + traits
- `reference-node/` — Minimal runnable node (`ss-node` binary, `cargo run -p sovereignstack-reference-node`)
- `conformance/` — Executable test suites for SIP/SEP/SAP/SMP + 4 conformance profiles
- `dashboard/` — React + Vite monitoring dashboard

#### Governance & Project Structure
- `GOVERNANCE.md` — TSC structure, Conformance WG, Standards WG
- `PROTOCOL_REGISTRY.md` — Protocol lifecycle tracking (Draft→Stable→Deprecated)
- `ROADMAP-2035.md` — 10-year vision (6 phases through Sovereign Intelligence Internet)
- `STANDARDS.md` — 6-layer standards framework
- `ANNOUNCEMENT.md` — v0.3.0 release announcement

### Changed
- `README.md` — Full RFC table (0001–0010), architecture diagram, badges
- `CONFORMANCE.md` — Badge specification, protocol registry, enhanced certification
- `CONTRIBUTING.md` — RFC process, standards ecosystem section
- All RFCs renumbered and upgraded to formal specifications

### Infrastructure
- 57 files, 4420+ lines added in standards ecosystem
- 36 files, 2623+ lines added in architecture + kernel + reference node
- 15 files, 1396+ lines added in RFCs 0004–0010

---

## [2026.1] — 2026-05-27

### Added
- OASA Conformance Test Suite (L1/L2/L3) — 38 conformance tests
- SVG badges for all conformance levels
- Certification JSON schemas (oasa-certification, oasa-conformance-report)
- Compliance report generator (`tools/generate_compliance_report.py`)
- Helm chart (`charts/sovereignstack/`) with NetworkPolicies, gVisor, vLLM
- Keycloak OIDC identity layer (`config/keycloak/sovereign-realm.json`)
- OpenTelemetry collector and Prometheus scraping
- STRIDE-based threat model (`docs/security/threat-model.md`)
- Architecture documentation (`ARCHITECTURE.md`, `docs/architecture/`, `docs/deployment/`)
- Governance model (`GOVERNANCE.md`)
- RFC process with first RFC (Runtime Spec)
- Repository standards (`ROADMAP.md`, `CODE_OF_CONDUCT.md`, `specs/`)

### Changed
- `docker-compose.yml` — Added Keycloak, OTel, Prometheus; health check ordering
- `services/gateway_service.py` — Real RS256/RS384/RS512 JWT validation via PyJWKClient
- `README.md` — Shields.io badges, benchmark tables, try-in-2-min flow
- `install.sh` — OASA 2026.1 format, prerequisite checks, model recommendations
- `.github/workflows/oasa-conformance.yml` — JUnit XML, dynamic badge JSON, concurrency groups
- `sovereign-stack.yaml` — Consolidated to OASA 2026.1 dual-format

### Fixed
- Schema auto-detection for old and new config formats
- Graceful psutil import fallback in runtime_shield.py
- Escape character bug in tools/sovereign_stack.py
