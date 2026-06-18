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
| **AFP** | AI Fabric Protocol | **Draft** | 0.1 | RFC-0032 | `ss-core/` (types) | Planned |
| **SLP** | Scheduling & Locality Protocol | **Draft** | 0.1 | RFC-0031 | `ss-core/` (types) | Planned |
| **FTP** | Fabric Telemetry Protocol | **Draft** | 0.1 | RFC-0033 | `ss-core/` (types) | Planned |
| **DKP** | Distributed KV Placement Protocol | **Draft** | 0.1 | RFC-0034 | `ss-core/` (types) | Planned |
| **TAF** | Topology-Aware Federation Protocol | **Draft** | 0.1 | RFC-0035 | `ss-core/` (types) | Planned |
| **MFO** | Memory Fabric Objects Protocol | **Draft** | 0.1 | RFC-0036 | `ss-core/` (types) | Planned |
| **ACP** | AI Cluster Profiles Protocol | **Draft** | 0.1 | RFC-0037 | `ss-core/` (types) | Planned |
| **MLP** | Model Lineage Protocol | **Draft** | 0.1 | RFC-0040 | `ss-core/` (types) | Planned |
| **JCE** | Jurisdiction Compliance Engine | **Draft** | 0.1 | RFC-0021 | `ss-jurisdiction/` | Planned |
| **AI-CDR** | AI Continuity & Disaster Recovery | **Draft** | 0.1 | RFC-0050 | `ss-core/` (types) | Planned |
| **MFP** | Model Failover Protocol | **Draft** | 0.1 | RFC-0051 | `ss-core/` (types) | Planned |
| **SRP** | Sovereign Recovery Profiles | **Draft** | 0.1 | RFC-0053 | `ss-core/` (types) | Planned |

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
| 2026-06-02 | AFP registered as Draft (RFC-0032 AI Fabric Protocol) |
| 2026-06-02 | SLP registered as Draft (RFC-0031 KV Locality Scheduling) |
| 2026-06-03 | FTP registered as Draft (RFC-0033 Fabric Telemetry Protocol) |
| 2026-06-03 | DKP registered as Draft (RFC-0034 Distributed KV Placement) |
| 2026-06-03 | TAF registered as Draft (RFC-0035 Topology-Aware Federation) |
| 2026-06-03 | MFO registered as Draft (RFC-0036 Memory Fabric Objects) |
| 2026-06-03 | ACP registered as Draft (RFC-0037 AI Cluster Profiles) |
| 2026-06-03 | MLP registered as Draft (RFC-0040 Model Lineage Protocol) |
| 2026-06-03 | AI-CDR registered as Draft (RFC-0050 AI Continuity & Disaster Recovery) |
| 2026-06-03 | MFP registered as Draft (RFC-0051 Model Failover Protocol) |
| 2026-06-03 | SRP registered as Draft (RFC-0053 Sovereign Recovery Profiles) |
