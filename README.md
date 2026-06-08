# SovereignStack

<p align="center">
  <img src="badges/sovereignstack-logo.svg" alt="SovereignStack" height="80">
</p>
<p align="center">
  <img src="badges/oasa-compatible.svg" alt="OASA Compatible" height="40">
  <img src="badges/oasa-l1-ready.svg" alt="L1 Sovereign-Ready" height="40">
  <img src="badges/oasa-l2-secure.svg" alt="L2 Secure-Runtime" height="40">
  <img src="badges/oasa-l3-strict.svg" alt="L3 Strict-Sovereign" height="40">
</p>
<p align="center">
  <strong>38 RFCs</strong> (0001–0040) · <strong>30 URI schemes</strong> · <strong>15 protocols</strong>
</p>

> **The Sovereign Intelligence Network** — A distributed operating system for intelligence.

[![Architecture Diagram](docs/architecture/diagrams/architecture-stack.svg)](docs/architecture/00-overview.md)

SovereignStack is a protocol stack and runtime that treats intelligence itself as a networked resource. It is to autonomous intelligence what TCP/IP is to data networking.

```
1970s → ARPANET          (packet switching)
1990s → Internet         (global connectivity)
2000s → Cloud            (elastic compute)
2020s → AI Platforms     (model serving)
2030s → Sovereign Intelligence Networks (SovereignStack)
```

## Design Principles

Every SovereignStack object is:

1. **Identifiable** — has a unique URI
2. **Addressable** — resolvable across the network
3. **Discoverable** — findable via capability/semantic search
4. **Verifiable** — cryptographically signed, with provenance
5. **Portable** — movable across nodes and jurisdictions
6. **Federatable** — shareable across sovereign boundaries
7. **Auditable** — full history and reasoning trail

## Universal Addressing

```
agent://researcher-1            # Agent identity
session://abc123                # Session
artifact://def456               # Produced artifact
memory://xyz789                 # Memory object
reason://decision-42            # Reasoning chain
knowledge://physics/newton      # Knowledge object
capability://legal-review       # Skill/capability
workflow://contract-analysis    # Workflow definition
contract://task-88              # Agent contract
org://acme                      # Organization
robot://drone-12                # Physical device
policy://gdpr-eu                # Governance policy
tel://zcube-a/evt-001           # Telemetry event (RFC-0033)
kv://zcube-a/gpu-003/session-a  # KV cache object (RFC-0034)
gateway://eu-frankfurt          # Federation gateway (RFC-0035)
mem://zcube-a/gpu-003/hbm       # Memory pool (RFC-0036)
profile://zcube-standard-v1     # Cluster profile (RFC-0037)
```

## Architecture

<p align="center">
  <img src="docs/architecture/diagrams/rfc-protocol-stack.svg" alt="Protocol Stack" width="85%">
  <br><em>SovereignStack Protocol Stack — RFCs organized by layer</em>
</p>

<p align="center">
  <img src="docs/architecture/diagrams/deployment-models.svg" alt="Deployment Models" width="85%">
  <br><em>Deployment Models: Air-gapped · Federated Mesh · Hybrid</em>
</p>

<p align="center">
  <img src="docs/architecture/diagrams/data-flow.svg" alt="Data Flow" width="85%">
  <br><em>OASA Data Flow — API Gateway → Inference → Audit Trail</em>
</p>

```
ss-kernel
 ├── Identity        (UAI, SIG, trust, reputation)
 ├── Capabilities    (registry, discovery, routing)
 ├── Messaging       (event bus, streams)
 ├── Memory          (tiered: session → civilizational)
 ├── Scheduling      (compute placement, model selection)
 ├── Federation      (sovereign routing, replication)
 ├── Governance      (policies, jurisdiction, compliance)
 └── Provenance      (lineage, evidence, audit)
```

## Core Features & Services

Alongside the core Rust primitives, SovereignStack implements a suite of Python-based microservices providing production-ready infrastructure:

- **OASA API Gateway**: Secure, OpenAI-compatible entry point enforcing Data Loss Prevention (DLP), Strict Compliance Locking, and SPIFFE workload identity validation.
- **Federation Relay & Sync Engine**: Decentralized node synchronization utilizing advanced Conflict-Free Replicated Data Types (CRDTs) to ensure eventual consistency across sovereign boundaries.
- **Merkle Audit Log**: Cryptographically verifiable, append-only event stream providing a tamper-proof provenance trail for all system operations.
- **Predictive Scheduler**: Autonomous operational controller employing exponential smoothing models to predict compute load and proactively scale resources.
- **Weight Federation**: Secure registration and sharding of model weights across distributed nodes for collaborative inference.

## Repository Structure

```
SovereignStack/
├── ss-kernel/        # Core kernel (identity, resolver, eventbus, registry, capability, policy)
├── ss-core/          # Shared types, URI parsing, errors
├── ss-crypto/        # Ed25519 signing, hashing
├── ss-identity/      # Universal Agent Identity
├── ss-capability/    # Capability declaration & matching
├── ss-eventbus/      # Event sourcing infrastructure
├── ss-cas/           # Content-addressed storage
├── ss-federation/    # Sovereign routing & discovery
├── ss-runtime/       # Multi-model execution runtime
├── ss-memory/        # Tiered memory subsystem (Stub)
├── ss-sessiond/      # Session lifecycle daemon
├── ss-scheduler/     # Compute placement (Stub)
├── ss-swarm/         # Multi-agent coordination (Stub)
├── ss-reason/        # Reasoning object store (Stub)
├── ss-kas/           # Knowledge addressing system (Stub)
├── ss-sig/           # Sovereign identity graph (Stub)
├── ss-trust/         # Trust framework (Stub)
├── ss-reputation/    # Reputation scoring (Stub)
├── ss-policy/        # Governance & jurisdiction (Stub)
├── ss-provenance/    # Computational lineage (Stub)
├── ss-jurisdiction/  # Jurisdiction compliance engine
├── ss-twin/          # Digital twin framework
├── ss-device/        # Reality interface layer (Stub)
├── ss-economy/       # Resource markets (Stub)
├── ss-sip/           # Sovereign Intelligence Protocol (Stub)
├── reference-node/   # Minimal reference node binary
├── conformance/      # Conformance test suites & profiles
├── rfcs/             # Protocol specifications (RFC-0001–0040)
├── docs/
│   ├── architecture/ # 10-page architecture breakdown
│   └── architecture/diagrams/ # SVG architecture diagrams
├── tests/            # Conformance test suite
├── examples/         # Reference implementations
└── playground/       # Try-it-now deployment
```

## Standards Ecosystem

SovereignStack is governed by a formal standards framework:

| Document | Description |
|---|---|
| [STANDARDS.md](STANDARDS.md) | Root standards framework — 6 layers |
| [OBJECT_MODEL.md](OBJECT_MODEL.md) | Universal object model with cryptographic signatures |
| [URI_STANDARD.md](URI_STANDARD.md) | URI scheme registry & resolution rules |
| [TRUST_MODEL.md](TRUST_MODEL.md) | Capability-based zero-trust security |
| [SECURITY.md](SECURITY.md) | Threat model & incident response |
| [CONFORMANCE.md](CONFORMANCE.md) | 3-tier certification program & badges |
| [CERTIFICATION.md](CERTIFICATION.md) | Badge levels, colors, shapes, materials |
| [PROTOCOL_REGISTRY.md](PROTOCOL_REGISTRY.md) | 7 protocols with lifecycle management |
| [REFERENCE_IMPLEMENTATIONS.md](REFERENCE_IMPLEMENTATIONS.md) | 13 core subsystems + 3 language bindings |
| [ROADMAP-2035.md](ROADMAP-2035.md) | 10-year vision through Sovereign Intelligence Internet |
| [BUILD_WINDOWS.md](BUILD_WINDOWS.md) | Windows build guide — exe, MSI, Python bundling |

### RFCs

| RFC | Title | Status |
|---|---|---|
| [RFC-0001](rfcs/RFC-0001-core-object-model.md) | Sovereign Object Model | Draft |
| [RFC-0002](rfcs/RFC-0002-uri-resolution.md) | URI Standard + ABNF Grammar | Draft |
| [RFC-0003](rfcs/RFC-0003-session-runtime.md) | Trust Graph | Draft |
| [RFC-0004](rfcs/RFC-0004-capability-registry.md) | Capability Registry | Draft |
| [RFC-0005](rfcs/RFC-0005-knowledge-objects.md) | Knowledge Objects | Draft |
| [RFC-0006](rfcs/RFC-0006-reasoning-objects.md) | Reasoning Objects | Draft |
| [RFC-0007](rfcs/RFC-0007-event-bus.md) | Event Bus | Draft |
| [RFC-0008](rfcs/RFC-0008-federation-routing.md) | Federation Routing | Draft |
| [RFC-0009](rfcs/RFC-0009-session-lifecycle.md) | Session Lifecycle | Draft |
| [RFC-0010](rfcs/RFC-0010-conformance-framework.md) | Conformance Framework | Draft |
| [RFC-0011](rfcs/RFC-0011-identity-did-resolution.md) | Identity & DID Resolution | Draft |
| [RFC-0012](rfcs/RFC-0012-cryptographic-signatures.md) | Cryptographic Signatures & Verification | Draft |
| [RFC-0013](rfcs/RFC-0013-provenance-graph.md) | Provenance Graph | Draft |
| [RFC-0014](rfcs/RFC-0014-agent-communication.md) | Agent Communication Protocol | Draft |
| [RFC-0015](rfcs/RFC-0015-workflow-execution.md) | Workflow Execution Engine | Draft |
| [RFC-0016](rfcs/RFC-0016-resource-allocation.md) | Resource Allocation & Accounting | Draft |
| [RFC-0017](rfcs/RFC-0017-sovereign-memory-protocol.md) | Sovereign Memory Protocol (Detailed) | Draft |
| [RFC-0018](rfcs/RFC-0018-content-addressed-storage.md) | Content-Addressable Storage | Draft |
| [RFC-0019](rfcs/RFC-0019-trust-reputation-scoring.md) | Trust & Reputation Scoring | Draft |
| [RFC-0020](rfcs/RFC-0020-policy-enforcement.md) | Policy Enforcement | Draft |
| [RFC-0021](rfcs/RFC-0021-jurisdiction-data-residency.md) | Jurisdiction & Data Residency | Draft |
| [RFC-0022](rfcs/RFC-0022-audit-log-streaming.md) | Audit Log Streaming | Draft |
| [RFC-0023](rfcs/RFC-0023-extension-plugin-system.md) | Extension & Plugin System | Draft |
| [RFC-0024](rfcs/RFC-0024-multi-model-routing.md) | Multi-Model Routing | Draft |
| [RFC-0025](rfcs/RFC-0025-session-migration.md) | Session Migration | Draft |
| [RFC-0026](rfcs/RFC-0026-capability-delegation.md) | Capability Delegation Chain | Draft |
| [RFC-0027](rfcs/RFC-0027-swarm-coordination.md) | Swarm Coordination | Draft |
| [RFC-0028](rfcs/RFC-0028-digital-twin-sync.md) | Digital Twin Synchronization | Draft |
| [RFC-0029](rfcs/RFC-0029-intelligence-economy.md) | Intelligence Economy Primitives | Draft |
| [RFC-0030](rfcs/RFC-0030-network-topology-awareness.md) | Network Topology Awareness | Draft |
| [RFC-0031](rfcs/RFC-0031-kv-locality-scheduling.md) | KV Locality Scheduling | Draft |
| [RFC-0032](rfcs/RFC-0032-ai-fabric-protocol.md) | AI Fabric Protocol | Draft |
| [RFC-0033](rfcs/RFC-0033-fabric-telemetry.md) | Fabric Telemetry Protocol | Draft |
| [RFC-0034](rfcs/RFC-0034-distributed-kv-placement.md) | Distributed KV Placement | Draft |
| [RFC-0035](rfcs/RFC-0035-topology-aware-federation.md) | Topology-Aware Federation | Draft |
| [RFC-0036](rfcs/RFC-0036-memory-fabric-objects.md) | Memory Fabric Objects | Draft |
| [RFC-0037](rfcs/RFC-0037-ai-cluster-profiles.md) | AI Cluster Profiles | Draft |
| [RFC-0040](rfcs/RFC-0040-model-lineage-protocol.md) | Model Lineage Protocol | Draft |

### Compliance & Audit

| Asset | Description |
|-------|-------------|
| [OASA CCM](compliance/oasa-ccm.md) | Core Controls Matrix — NET, RUN, HW, AUD controls for L1/L2/L3 certification |
| [Compliance Schema](schemas/oasa-compliance.schema.json) | JSON Schema (Draft 2020-12) for automated node validation |
| [Audit Evidence Schema](schemas/oasa-audit-evidence.schema.json) | JSON Schema for `oasa-audit report` evidence packages |
| [Validation Script](tools/validate_compliance.py) | Automated compliance scanner with `--audit-host` and `--generate-template` |

## Quickstart

```bash
# Clone & enter
git clone https://github.com/Kubenew/SovereignStack.git
cd SovereignStack

# Windows: build .exe binaries (see BUILD_WINDOWS.md for full MSI guide)
cargo build --release --bin ss-node --bin ss-cli

# Launch playground (Docker Compose)
docker compose -f playground/docker-compose.yml up -d

# Or build from source
cargo build --workspace
```

### Test

```bash
cargo test --workspace
```

## License

Apache-2.0 OR MIT (dual-licensed)
