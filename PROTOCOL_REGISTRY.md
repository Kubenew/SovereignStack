# SovereignStack Protocol Registry

**Version:** 2026.1
**Last Updated:** May 31, 2026
**Maintained by:** OASA Technical Steering Committee

## Purpose

This registry tracks the lifecycle status of every protocol in the SovereignStack ecosystem. It enables ecosystem participants to understand which protocols are stable, experimental, or deprecated.

## Protocols

| ID | Protocol Name | Status | Version | RFC | Reference Implementation | Conformance Suite |
|----|--------------|--------|---------|-----|------------------------|-----------------|
| **SIP** | Sovereign Intelligence Protocol | **Stable** | 1.0 | RFC-0004 | `ss-sip/` | `conformance/tests/sip/` |
| **SEP** | Sovereign Extension Protocol | **Draft** | 0.1 | RFC-0005 | `ss-extension/` | `conformance/tests/sep/` |
| **SAP** | Sovereign Agent Protocol | **Draft** | 0.1 | RFC-0006 | `ss-sessiond/` | `conformance/tests/sap/` |
| **SMP** | Sovereign Memory Protocol | **Draft** | 0.1 | — | `ss-memory/` | `conformance/tests/smp/` |
| **KAP** | Sovereign Knowledge Access Protocol | **Draft** | 0.1 | RFC-0006 | `ss-kas/` | Planned |
| **REP** | Sovereign Reasoning Exchange Protocol | **Draft** | 0.1 | — | `ss-reason/` | Planned |
| **TAP** | Topology Awareness Protocol | **Draft** | 0.1 | RFC-0030 | `ss-core/` (types) | Planned |

## Protocol Lifecycle

```
Draft → Experimental → Beta → Stable → Deprecated → Historic
```

### Lifecycle Requirements

| Stage | Requirements |
|-------|-------------|
| **Draft** | Published RFC, initial concept |
| **Experimental** | Proof-of-concept implementation, basic tests |
| **Beta** | Reference implementation, conformance test suite, 2+ compatible implementations |
| **Stable** | Multiple interoperable implementations, security review, 6+ months in Beta |
| **Deprecated** | Superseded by newer version, 12-month migration window |
| **Historic** | No longer in use, documentation archived |

## Lifecycle Transitions

| From | To | Requires |
|------|----|----------|
| Draft | Experimental | RFC accepted, PoC passes smoke tests |
| Experimental | Beta | Reference implementation + conformance suite |
| Beta | Stable | 2 implementations interoperable, security audit |
| Stable | Deprecated | TSC vote, migration plan published |
| Deprecated | Historic | 12 months after deprecation |

## How to Add a Protocol

1. Submit an RFC following [RFC-0000](rfcs/0000-rfc-process.md)
2. Provide a protocol identifier (3–4 uppercase letters)
3. Implement a proof-of-concept
4. Submit a PR adding your protocol to this registry

## Change Log

| Date | Change |
|------|--------|
| 2026-05-31 | SIP promoted to Stable |
| 2026-05-31 | SEP, SAP, SMP registered as Draft |
| 2026-05-31 | KAP, REP registered as Draft |
| 2026-06-02 | TAP registered as Draft (RFC-0030 Network Topology Awareness) |
