# RFC-0010: Conformance Framework

**Status:** Draft
**Type:** Process
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the conformance testing framework — the automated test suites, conformance profiles, certification levels, and attestation format that implementations must satisfy to claim OASA compliance.

## Motivation

Without conformance testing, standards are aspirational. This framework ensures that every implementation claiming OASA compatibility can be verified automatically, reproducibly, and independently.

## Specification

### Conformance Profiles

Profiles define which tests an implementation must pass to claim a given conformance level:

```yaml
# profiles/core-node.yaml
profile:
  id: core-node
  name: Core Node
  version: "1.0"
  description: "Minimal SovereignStack node with kernel services"
  requires:
    - sip:
        handshake: required
        ping: required
        capability_exchange: required
        message_roundtrip: required
    - sap:
        agent_registration: required
        agent_query: required
    - smp:
        memory_store: required
        memory_retrieve: required
    - rfc-0001: # Object Model
        object_create: required
        object_sign: required
        object_query: required
        object_exchange: required
        object_audit: required
  protocol_level: L1
```

```yaml
# profiles/federation-node.yaml
profile:
  id: federation-node
  name: Federation Node
  version: "1.0"
  extends: core-node
  description: "Core node with federation capabilities"
  requires:
    - sip:
        subscribe: required
    - sep:
        extension_registration: required
        extension_discovery: required
    - rfc-0008: # Federation Routing
        peer_discovery: required
        trust_negotiation: required
        data_replication: required
  protocol_level: L2
```

```yaml
# profiles/knowledge-node.yaml
profile:
  id: knowledge-node
  name: Knowledge Node
  version: "1.0"
  extends: core-node
  description: "Core node with knowledge and reasoning services"
  requires:
    - kap:
        knowledge_create: required
        knowledge_query: required
        knowledge_version: required
    - rep:
        reason_record: required
        reason_replay: required
    - rfc-0005: # Knowledge Objects
        evidence_linking: required
        trust_scoring: required
    - rfc-0006: # Reasoning Objects
        step_verification: required
  protocol_level: L2
```

```yaml
# profiles/agent-node.yaml
profile:
  id: agent-node
  name: Agent Node
  version: "1.0"
  extends: core-node
  description: "Core node optimized for agent execution"
  requires:
    - sap:
        agent_message: required
        agent_session_create: required
        agent_session_terminate: required
    - smp:
        memory_search: required
        memory_ttl: required
    - rfc-0009: # Session Lifecycle
        session_suspend_resume: required
        resource_enforcement: required
        capability_scoping: required
  protocol_level: L2
```

### Certification Levels

| Level | Profile | Test Count | Audit Required | Badge |
|-------|---------|------------|----------------|-------|
| L1 | core-node | 15 | No | Shield (Silver) |
| L2 | Any extended profile | 30 | Self-certified | Hexagon (Gold) |
| L3 | All profiles | 60+ | Third-party | Star (Diamond) |

### Test Suite Structure

```
conformance/
├── tests/
│   ├── sip/           # SIP protocol tests
│   ├── sep/           # SEP protocol tests
│   ├── sap/           # SAP protocol tests
│   ├── smp/           # SMP protocol tests
│   ├── kap/           # KAP protocol tests (planned)
│   ├── rep/           # REP protocol tests (planned)
│   └── rfc/           # RFC-specific tests
│       ├── 0001-object-model/
│       ├── 0002-uri-standard/
│       ├── 0003-trust-graph/
│       ├── 0004-capability-registry/
│       ├── 0005-knowledge-objects/
│       ├── 0006-reasoning-objects/
│       ├── 0007-event-bus/
│       ├── 0008-federation-routing/
│       ├── 0009-session-lifecycle/
│       └── 0010-conformance-framework/
├── fixtures/          # Test data files
├── profiles/          # Conformance profile YAMLs
└── certifications/    # Generated attestations
```

### Test Execution

```bash
# Run all tests for a profile
python -m pytest tests/ --profile core-node -v

# Run specific RFC conformance
python -m pytest tests/rfc/0001-object-model/ -v

# Generate certification report
python tools/generate_report.py --profile knowledge-node --output report.md

# Validate attestation
python tools/validate_attestation.py certifications/attestation.json
```

### Attestation Format

```json
{
  "oasa_version": "2026.1",
  "certification": {
    "profile": "knowledge-node",
    "level": "L2",
    "status": "active",
    "issued": "2026-05-31T00:00:00Z",
    "expires": "2027-05-31T00:00:00Z"
  },
  "subject": {
    "name": "Implementation Name",
    "version": "1.0.0",
    "type": "knowledge-node"
  },
  "tests": {
    "suites": {
      "sip": {"passed": 8, "failed": 0, "skipped": 0},
      "kap": {"passed": 6, "failed": 0, "skipped": 0},
      "rep": {"passed": 4, "failed": 0, "skipped": 0},
      "rfc-0001": {"passed": 5, "failed": 0, "skipped": 0},
      "rfc-0005": {"passed": 7, "failed": 0, "skipped": 0},
      "rfc-0006": {"passed": 6, "failed": 0, "skipped": 0}
    },
    "total_passed": 36,
    "total_failed": 0,
    "total_skipped": 0,
    "suite_version": "1.0"
  },
  "evidence": {
    "security_audit": null,
    "sbom": "https://example.com/sbom.spdx.json",
    "ci_run": "https://ci.example.com/runs/1234",
    "attestation_signature": "sig:attestation-abc..."
  }
}
```

### Running a Conformance Program

1. **Implement** a SovereignStack node
2. **Select** a conformance profile
3. **Run** the test suite against the implementation
4. **Generate** attestation JSON
5. **Submit** to OASA registry
6. **Receive** badge (if passed)
7. **Renew** annually

## Transition to Stable

This RFC reaches Stable when:
- 3+ independent implementations pass L1 conformance
- 2+ implementations pass L2 conformance
- CI pipeline runs tests automatically
- Attestation format is validated by independent implementations

## Reference Implementation

- `conformance/` directory — test suites and profiles
- CI pipeline: `.github/workflows/oasa-conformance.yml`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
