# SovereignStack Architecture

**Revision:** 1.0 — May 2026  
**Status:** Living Document

---

## 1. System Overview

SovereignStack is a layered sovereign AI infrastructure platform. Each layer has well-defined boundaries, APIs, and security contracts. Data flows strictly upward through authenticated, policy-enforced gateways.

```
                    ┌──────────────────────────────────────┐
                    │           APPLICATIONS                │
                    │  OpenAI SDK / LangChain / Custom App  │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │         AUTONOMOUS AGENTS            │
                    │  Lifecycle · Scheduling · Memory     │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │         AI RUNTIME LAYER             │
                    │  vLLM · llama.cpp · Model Router     │
                    │  INT4/AWQ/FP8 · PagedAttention       │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │     MEMORY & COORDINATION            │
                    │  Vector Store · KV Cache · Sync      │
                    │  AES-256-GCM · TPM Binding           │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │      IDENTITY & SECURITY             │
                    │  Keycloak OIDC · OPA Policy · RBAC   │
                    │  mTLS · SPIFFE/SPIRE · JWT           │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │    FEDERATION & MESH NETWORKING      │
                    │  Inter-node Sync · Discovery · Route │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │      CONTAINER / VM RUNTIME          │
                    │  Docker · K3s · gVisor · Kata        │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │       HOST OPERATING SYSTEM          │
                    │  Linux · Talos · NixOS · CoreOS      │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │            HARDWARE                  │
                    │  NVIDIA CUDA · Apple Metal · CPU     │
                    │  TPM 2.0 · SGX · SEV-SNP             │
                    └──────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Sovereign Runtime

The AI execution layer. Responsible for model loading, inference, scheduling, and resource isolation.

| Component | Role | Technology |
|---|---|---|
| **Inference Engine** | Model execution | vLLM, llama.cpp |
| **Model Router** | Request routing by model/role | Gateway service |
| **Scheduler** | GPU memory + request queue | vLLM PagedAttention |
| **Sandbox** | Runtime isolation | gVisor, Kata Containers |

### 2.2 Memory & Coordination Layer

Persistent, encrypted, distributed memory for vectors, KV caches, and state synchronization.

| Component | Role | Technology |
|---|---|---|
| **Vector Store** | Embedding storage & retrieval | Local JSON / Qdrant |
| **KV Cache** | Context caching | vLLM cache |
| **Sync Engine** | Cross-node state replication | CRDT / Event log |
| **Encryption** | Data-at-rest protection | AES-256-GCM + TPM |

### 2.3 Identity & Security Layer

Zero-trust identity for nodes, workloads, and users.

| Component | Role | Technology |
|---|---|---|
| **OIDC Provider** | User authentication | Keycloak |
| **Policy Engine** | Access & DLP governance | Open Policy Agent |
| **Node Identity** | Hardware attestation | TPM 2.0, SPIFFE/SPIRE |
| **Audit Log** | Immutable event record | Append-only JSON log |

### 2.4 Federation & Mesh Layer

Inter-node communication, discovery, and synchronization for multi-node deployments.

| Component | Role | Technology |
|---|---|---|
| **Mesh Router** | Inter-node traffic | WireGuard / Tailscale |
| **Discovery** | Node & service discovery | DNS-SD / Consul |
| **Federation** | Cross-cluster sync | CRDT / gRPC |
| **Offline Sync** | Disconnected operation | Event sourcing |

---

## 3. Trust Boundaries

```
  ┌────────────────────────────────────────────────────────┐
  │                   PUBLIC / CLIENT NET                   │
  │  TLS 1.3 — Authenticated via OIDC bearer token         │
  └────────────────────┬───────────────────────────────────┘
                       │
                ┌──────▼──────┐
                │ TRUST       │  Gateway validates JWT,
                │ BOUNDARY 1  │  evaluates OPA policy,
                │             │  logs to audit.
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
  ┌─────▼─────┐ ┌──────▼──────┐ ┌─────▼─────┐
  │ COMPUTE   │ │ MEMORY     │ │ INGEST    │
  │ Sandbox   │ │ Encrypted  │ │ RAM-Only  │
  │ gVisor    │ │ AES-256    │ │ Volatile  │
  │ No egress │ │ TPM-bound  │ │ No disk   │
  └─────┬─────┘ └──────┬──────┘ └─────┬─────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                ┌──────▼──────┐
                │ TRUST       │  TPM-bound encryption keys,
                │ BOUNDARY 2  │  immutable audit zone,
                │             │  physical access required.
                └─────────────┘
```

---

## 4. Data Flow

### 4.1 Chat Completion

```
Client → Gateway → [Auth: OIDC JWT] → [Policy: OPA DLP]
        → [Compliance Lock Check] → [RAG: Memory Query]
        → [Inference: vLLM] → [Audit Log] → Response
```

### 4.2 Document Ingestion

```
Client → Ingest → [SHA-256 Hash] → [Volatile RAM Parse]
        → [Schema Validate] → [Encrypted Storage] → Response
```

### 4.3 Federation Sync

```
Node A → [CRDT Merge] → Node B
       ← [State Digest] ←
```

---

## 5. Deployment Profiles

| Profile | Target | Compute | Storage | Network |
|---|---|---|---|---|
| **Edge** | ARM devices, IoT | CPU inference | Local SQLite | Disconnected |
| **Air-Gapped** | Isolated networks | GPU + CPU | AES-256 + TPM | No WAN egress |
| **Datacenter** | GPU clusters | Multi-GPU vLLM | Distributed DB | Internal fabric |
| **Personal** | Laptop, homelab | CPU/GPU | Local FS | Optional VPN |

---

## 6. API Contracts

| Endpoint | Protocol | Auth | Purpose |
|---|---|---|---|
| `POST /v1/chat/completions` | HTTP | OIDC Bearer | Inference (OpenAI-compatible) |
| `POST /ingest` | HTTP | OIDC Bearer | Document ingestion |
| `POST /embed` | HTTP | Internal | Vector embedding |
| `POST /query` | HTTP | Internal | Memory retrieval |
| `GET /health` | HTTP | None | Health check |

---

## 7. Related Documents

- [OASA Specification](OASA.md) — Protocol and axiom definitions
- [Threat Model](docs/security/threat-model.md) — STRIDE threat catalogue
- [Deployment Guide](docs/deployment/) — Profile-specific instructions
- [RFC Process](rfcs/) — Standards evolution
- [Governance Model](GOVERNANCE.md) — Project structure
