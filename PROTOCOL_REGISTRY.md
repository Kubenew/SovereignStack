# SovereignStack Protocol Registry

**Version:** 2026.2
**Last Updated:** July 16, 2026
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
| | | | | | | |
| | **— Cognitive Mesh Family (SIRA) —** | | | | | |
| **CRP** | Cognitive Router Protocol | **Draft** | 0.1 | RFC-0061 | `ss-routing/` | Planned |
| **SXP** | Session Exchange Protocol | **Draft** | 0.1 | RFC-0062 | `ss-sessiond/` | Planned |
| **DMP** | Distributed Memory Protocol | **Draft** | 0.1 | RFC-0063 | `ss-memory/` | Planned |
| **AFS** | AI Fabric Scheduling Protocol | **Draft** | 0.1 | RFC-0064 | `ss-scheduler/` | Planned |
| **CDP** | Capability Delegation Protocol | **Draft** | 0.1 | RFC-0065 | `ss-capability/` | Planned |
| **CEB** | Cognitive Event Bus Protocol | **Draft** | 0.1 | RFC-0066 | `ss-eventbus/` | Planned |
| **CKP** | Checkpoint & Recovery Protocol | **Draft** | 0.1 | RFC-0067 | `ss-sessiond/` | Planned |
| **MAC** | Multi-Agent Consensus Protocol | **Draft** | 0.1 | RFC-0068 | `ss-swarm/` | Planned |
| **SMR** | Semantic Routing Protocol | **Draft** | 0.1 | RFC-0069 | `ss-routing/` | Planned |
| | | | | | | |
| | **— Meta-Cognition & Governance Family —** | | | | | |
| **MCP** | Meta-Cognition Protocol | **Draft** | 0.1 | RFC-0045 | `ss-memory/proto/meta_cognition.proto` | Planned |
| **GVP** | Governance Protocol | **Draft** | 0.1 | RFC-0046 | `ss-core/` (URI) | Planned |
| **DTP** | Digital Twin Protocol | **Draft** | 0.1 | RFC-0047 | `ss-core/` (URI) | Planned |
| **FMP** | Federation Mesh Protocol | **Draft** | 0.1 | RFC-0048 | `ss-swarm/` | Planned |
| **WMP** | World Model & Planning Protocol | **Draft** | 0.1 | RFC-0049 | `ss-core/` (URI) | Planned |
| **CLP** | Cognitive Lease Protocol | **Draft** | 0.1 | RFC-0050 | `ss-policy/src/circuit_breaker.rs` | `scripts/test_cognitive_leases.py` |
| **XPP** | Explainability & Provenance Protocol | **Draft** | 0.1 | RFC-0051 | `ss-core/` (URI) | Planned |
| **SRF** | Safe Resource Fencing Protocol | **Draft** | 0.1 | RFC-0052 | `ss-core/` (URI) | Planned |
| **HLP** | Human-in-the-Loop Priority Protocol | **Draft** | 0.1 | RFC-0053 | `ss-policy/src/proof_verifier.rs` | `charts/.../configmap-human.yaml` |
| **CNP** | Capability Negotiation Protocol | **Draft** | 0.1 | RFC-0054 | `ss-swarm/src/negotiation.rs` | Planned |
| **CBP** | Circuit Breaker Policy Protocol | **Draft** | 0.1 | RFC-0055 | `ss-policy/src/circuit_breaker.rs` | `scripts/test_mesh_degradation.py` |
| **ZAP** | Zero-Knowledge Alignment Protocol | **Draft** | 0.1 | RFC-0056 | `ss-policy/src/zk_alignment.rs` | `scripts/generate_alignment_proof.py` |
| **ASP** | Alignment Streamer Protocol | **Draft** | 0.1 | RFC-0057 | `ss-memory/src/grpc_server.rs` | `ss-memory/proto/mind_sync.proto` |

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
 | 2026-07-16 | Cognitive Mesh family registered: CRP, SXP, DMP, AFS, CDP, CEB, CKP, MAC, SMR (SIRA v1.0) |
| 2026-07-16 | **Meta-Cognition Protocol** (MCP) registered as Draft (RFC-0045) |
| 2026-07-16 | **Governance Protocol** (GVP) registered as Draft (RFC-0046) |
| 2026-07-16 | **Digital Twin Protocol** (DTP) registered as Draft (RFC-0047) |
| 2026-07-16 | **Federation Mesh Protocol** (FMP) registered as Draft (RFC-0048) |
| 2026-07-16 | **World Model & Planning Protocol** (WMP) registered as Draft (RFC-0049) |
| 2026-07-16 | **Cognitive Lease Protocol** (CLP) registered as Draft (RFC-0050) |
| 2026-07-16 | **Explainability & Provenance Protocol** (XPP) registered as Draft (RFC-0051) |
| 2026-07-16 | **Safe Resource Fencing Protocol** (SRF) registered as Draft (RFC-0052) |
| 2026-07-16 | **Human-in-the-Loop Priority Protocol** (HLP) registered as Draft (RFC-0053) |
| 2026-07-16 | **Capability Negotiation Protocol** (CNP) registered as Draft (RFC-0054) |
| 2026-07-16 | **Circuit Breaker Policy Protocol** (CBP) registered as Draft (RFC-0055) |
| 2026-07-16 | **Zero-Knowledge Alignment Protocol** (ZAP) registered as Draft (RFC-0056) |
| 2026-07-16 | **gRPC Alignment Streamer Protocol** (ASP) registered as Draft (RFC-0057) |
