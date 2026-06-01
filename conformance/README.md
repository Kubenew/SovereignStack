# SovereignStack Conformance Test Suite

**Repository:** `sovereignstack-conformance`
**Status:** Draft
**Version:** 2026.1

## Overview

This repository contains executable conformance test suites for every SovereignStack protocol. Passing these tests is required for OASA certification at any level.

## Structure

```
conformance/
├── tests/
│   ├── sip/          # Sovereign Intelligence Protocol
│   ├── sep/          # Sovereign Extension Protocol
│   ├── sap/          # Sovereign Agent Protocol
│   ├── smp/          # Sovereign Memory Protocol
│   └── rfc/          # RFC-specific conformance
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
├── fixtures/         # Test data and mock objects
├── profiles/         # Conformance profiles (RFC-0010)
└── certifications/  # Generated certification attestations
```

## Quick Start

```bash
# Run all conformance tests
python -m pytest tests/ -v

# Run a specific protocol suite
python -m pytest tests/sip/ -v

# Run RFC-specific conformance
python -m pytest tests/rfc/0001-object-model/ -v

# Run by profile
python -m pytest tests/ --profile core-node -v

# Generate certification report
python tools/generate_report.py --profile knowledge-node --output report.md
```

## Protocols Under Test

| Protocol | Status | Tests | Suite |
|---|---|---|---|
| SIP | Stable | 24 | tests/sip/ |
| SEP | Draft | 12 | tests/sep/ |
| SAP | Draft | 18 | tests/sap/ |
| SMP | Draft | 15 | tests/smp/ |

## RFC Conformance

| RFC | Title | Test Dir |
|-----|-------|----------|
| 0001 | Sovereign Object Model | tests/rfc/0001-object-model/ |
| 0002 | URI Standard | tests/rfc/0002-uri-standard/ |
| 0003 | Trust Graph | tests/rfc/0003-trust-graph/ |
| 0004 | Capability Registry | tests/rfc/0004-capability-registry/ |
| 0005 | Knowledge Objects | tests/rfc/0005-knowledge-objects/ |
| 0006 | Reasoning Objects | tests/rfc/0006-reasoning-objects/ |
| 0007 | Event Bus | tests/rfc/0007-event-bus/ |
| 0008 | Federation Routing | tests/rfc/0008-federation-routing/ |
| 0009 | Session Lifecycle | tests/rfc/0009-session-lifecycle/ |
| 0010 | Conformance Framework | tests/rfc/0010-conformance-framework/ |
