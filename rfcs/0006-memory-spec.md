# RFC 0006: Memory Specification

| Field | Value |
|---|---|
| **Status** | Draft |
| **Author** | SovereignStack Core Team |
| **Created** | 2026-05-27 |
| **Category** | Standards Track |

---

## Summary

Define the Sovereign Memory layer — the persistent, encrypted, distributed storage subsystem responsible for vector embeddings, KV cache management, event log replication, and cross-node state synchronization. The memory layer provides the foundation for RAG, session persistence, audit trails, and CRDT-based federation sync.

---

## Motivation

The current memory implementation is a single-service JSON backend with no formal specification. As the project grows toward multi-node federation and agent workloads, a standard memory model is needed to:

- Decouple the memory API from the storage backend (local JSON, Qdrant, PostgreSQL)
- Define consistent encryption, TTL, and isolation semantics
- Enable CRDT-based cross-node synchronization of vector indices and event logs
- Support agent memory attachment with scoped read/write/append access
- Provide at-rest encryption guarantees required for GDPR/HIPAA compliance

---

## Design

### Subsystem Architecture

```
                    ┌──────────────────────────────┐
                    │        GATEWAY / AGENT         │
                    │  POST /embed · POST /query     │
                    └────────────┬─────────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                  │
      ┌────────▼────────┐  ┌────▼───────┐  ┌──────▼────────┐
      │   VECTOR STORE   │  │ KV CACHE   │  │  EVENT LOG     │
      │                  │  │            │  │                │
      │  doc_id, vector  │  │ session_id,│  │  event_id,     │
      │  metadata, org   │  │ context,   │  │  action, actor,│
      │  timestamp       │  │ TTL        │  │  signature     │
      └────────┬─────────┘  └─────┬──────┘  └───────┬────────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │      STORAGE ENGINE      │
                     │  Local JSON | Qdrant |   │
                     │  PostgreSQL (pluggable)  │
                     └────────────┬────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │      ENCRYPTION          │
                     │  AES-256-GCM per doc     │
                     │  TPM 2.0 key binding     │
                     └─────────────────────────┘
```

### Storage Backends

| Backend | Profile | Persistence | Scalability |
|---|---|---|---|
| **Local JSON** | Personal, Edge | File-based | Single node |
| **Qdrant** | Air-Gapped, Datacenter | Disk + WAL | Multi-node |
| **PostgreSQL + pgvector** | Datacenter | ACID | Multi-node with HA |

Backend selection is configuration-only — the API contract is identical across all backends.

### API Contract

#### Vector Store

```
POST /embed       → Store document embedding
POST /query       → Semantic search (top-k)
DELETE /embed     → Remove document
POST /clear       → Clear all vectors (admin)
POST /backup      → Trigger snapshot backup
```

#### Embed Request

```json
{
  "doc_id": "doc-123",
  "text": "Document content to embed",
  "org_id": "default",
  "metadata": {"source": "pdf", "page": 42},
  "ttl_seconds": null
}
```

#### Query Request

```json
{
  "query": "What does the contract say about data residency?",
  "org_id": "default",
  "top_k": 3,
  "min_score": 0.65,
  "filter": {"source": "pdf"}
}
```

#### KV Cache

```
POST /cache/set    → Store context with TTL
GET  /cache/get    → Retrieve context by session_id
POST /cache/clear  → Expire all entries for org
```

#### Event Log

```
GET  /events       → Query events by time range / actor
POST /events/export → Export audit events to file
```

### Data Model

#### Vector Document

```json
{
  "doc_id": "doc-123",
  "org_id": "default",
  "embedding": [0.012, -0.034, ...],
  "metadata": {"source": "pdf", "page": 42},
  "created_at": "2026-05-27T09:00:00Z",
  "ttl_seconds": null,
  "encryption_iv": "a1b2c3d4e5f6g7h8",
  "checksum": "sha256:e4f8..."
}
```

#### Cache Entry

```json
{
  "session_id": "sess-4f8a",
  "context": "Relevant context text...",
  "ttl_until": "2026-05-27T10:00:00Z",
  "org_id": "default"
}
```

#### Event Log Entry

```json
{
  "event_id": "evt-9102",
  "timestamp": "2026-05-27T09:00:00Z",
  "node_id": "eu-fr1-a7f3b2c1",
  "actor": "gateway",
  "action": "memory.vector.upsert",
  "data": {"doc_id": "doc-123"},
  "signature": "MEUCIQD..."
}
```

### Encryption Specification

All vector data at rest MUST be encrypted:

| Parameter | Value |
|---|---|
| Algorithm | AES-256-GCM |
| Key derivation | HKDF-SHA256 from node identity key |
| IV length | 12 bytes (random, per document) |
| Tag length | 16 bytes |
| TPM binding | Key wrapped by TPM 2.0 SRK (when available) |
| Fallback | Encrypted key file at `/etc/sovereign/memory.key` |

### Synchronization (CRDT)

Event log entries are the source of truth for cross-node sync. Vector indices are reconstructed by replaying events.

| Event Type | CRDT Strategy |
|---|---|
| `memory.vector.upsert` | LWW-Register (doc_id as key) |
| `memory.vector.delete` | Tombstone Set |
| `cache.set` | LWW-Register (session_id as key) |

### Resource Limits

| Resource | Default | Enforcement |
|---|---|---|
| Max vectors per org | 100,000 | Configurable |
| Max vector dimensions | 4096 | Schema validation |
| Max context TTL | 86,400s (24h) | Server-side expiry |
| Max event log size | 1 GB | Rotation with archival |
| Max concurrent queries | 10 | Connection pool |

---

## Security Considerations

| Threat | Mitigation |
|---|---|
| Data at rest exposure | AES-256-GCM per document, TPM-bound keys |
| Memory injection (prompt) | Input validation at gateway layer |
| Cross-org data leakage | org_id isolation enforced at query layer |
| Event log tampering | Merkle chain (planned), signature verification |
| Replay of sync events | Monotonic sequence numbers per node |

---

## Compatibility

- JSON backend is the default and works with existing deployments
- Qdrant and PostgreSQL backends require no code changes — only config
- Event log format is backward compatible with existing audit logs
- CRDT sync is additive — single-node deployments ignore sync events

---

## Deployment Strategy

| Phase | Scope |
|---|---|
| Phase 1 | Local JSON backend, AES-256-GCM encryption, KV cache |
| Phase 2 | Vector query filtering, metadata storage, TTL enforcement |
| Phase 3 | Qdrant backend support, CRDT event log, backup/restore |
| Phase 4 | PostgreSQL backend, cross-node vector sync, Merkle audit chain |

---

## Migration Path

Existing `memory_service.py` using JSON backend continues unchanged. To enable encryption on existing data:

```bash
# 1. Backup existing data
cp data/memory/vectors.json data/memory/vectors.json.bak

# 2. Enable encryption in sovereign-stack.yaml
cognitive_memory:
  encryption_at_rest: true

# 3. Restart (service re-encrypts on first write)
docker compose restart memory
```

---

## Alternatives Considered

| Alternative | Reason Not Selected |
|---|---|
| Single global vector store | Violates air-gapped sovereignty model |
| Cloud-only memory (Pinecone) | WAN dependency, no offline mode |
| No memory isolation | Cross-org data leakage |
| Custom encryption per backend | Complexity; AES-256-GCM is universal |

---

## References

- [AES-GCM Specification (NIST)](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf)
- [CRDT Paper (Shapiro et al.)](https://hal.science/inria-00555588/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [pgvector](https://github.com/pgvector/pgvector)
