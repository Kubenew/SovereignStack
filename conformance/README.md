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
│   └── smp/          # Sovereign Memory Protocol
├── fixtures/         # Test data and mock objects
├── profiles/         # Implementation capability profiles
└── certifications/  # Generated certification attestations
```

## Quick Start

```bash
# Run all conformance tests
python -m pytest tests/ -v

# Run a specific protocol suite
python -m pytest tests/sip/ -v

# Generate certification report
python tools/generate_report.py --level L2 --output report.md
```

## Protocols Under Test

| Protocol | Status | Tests | Suite |
|---|---|---|---|
| SIP | Stable | 24 | tests/sip/ |
| SEP | Draft | 12 | tests/sep/ |
| SAP | Draft | 18 | tests/sap/ |
| SMP | Draft | 15 | tests/smp/ |
