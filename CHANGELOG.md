# Changelog

All notable changes to SovereignStack are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project uses [Calendar Versioning](https://calver.org) (`YYYY.N`).

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
