# Sovereign Memory Layer

The memory layer provides persistent, encrypted, distributed storage for vector embeddings, KV caches, and state synchronization across sovereign nodes.

---

## Architecture

```
                    ┌──────────────────────────────┐
                    │      GATEWAY / RUNTIME        │
                    │  Reads context, stores docs   │
                    └────────────┬─────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
     │   VECTOR STORE   │ │  KV CACHE   │ │   EVENT LOG     │
     │  Embeddings      │ │  Context    │ │  State changes  │
     │  Similarity      │ │  Session    │ │  Replay/Recover │
     │  AES-256-GCM     │ │  TTL 3600s  │ │  Append-only    │
     └────────┬────────┘ └─────────────┘ └────────┬────────┘
              │                                    │
              └────────────────┬───────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   SYNC ENGINE        │
                    │  CRDT Merge, Gossip  │
                    │  Cross-node Replic.  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ENCRYPTION         │
                    │  AES-256-GCM         │
                    │  TPM 2.0 Key Binding │
                    └─────────────────────┘
```

---

## Components

### Vector Store

Stores document embeddings for semantic search and RAG.

| Property | Value |
|---|---|
| Backend | Local JSON / Qdrant |
| Dimensions | 4096 (configurable) |
| Encryption | AES-256-GCM at rest |
| Indexing | HNSW (Qdrant) / linear scan (JSON) |

### KV Cache

Caches recent inference context for fast retrieval.

| Property | Value |
|---|---|
| Storage | In-memory + disk |
| TTL | 3600 seconds (configurable) |
| Isolation | Per-request session isolation |
| Eviction | LRU when memory threshold reached |

### Event Log

Append-only log of all state changes for auditing and recovery.

| Property | Value |
|---|---|
| Storage | Append-only JSON |
| Integrity | Merkle-tree chaining (planned) |
| Rotation | Size-based with archival |

---

## API Contract

### `POST /embed`

Store a document embedding.

```json
{
  "doc_id": "doc-123",
  "text": "Document content to embed",
  "org_id": "default"
}
```

### `POST /query`

Retrieve relevant context.

```json
{
  "query": "What does the contract say about data residency?",
  "org_id": "default",
  "top_k": 3
}
```

### `GET /health`

```json
{"status": "ok", "service": "memory", "vectors": 42, "cached_contexts": 12}
```

---

## Encryption

All data at rest is encrypted with AES-256-GCM. Encryption keys are:

1. Generated per-node at first boot
2. Bound to TPM 2.0 hardware (if available)
3. Stored in encrypted keyfile (software fallback)

```yaml
cognitive_memory:
  encryption_at_rest: true
  encryption_algorithm: "AES-256-GCM"
  hardware_tpm_binding: true
```

---

## Synchronization

Multi-node memory synchronization uses CRDTs (Conflict-Free Replicated Data Types) for eventual consistency without central coordination.

| Operation | Strategy | Consistency |
|---|---|---|
| Write | Local-first | Eventual |
| Read | Local | Strong (local) |
| Sync | CRDT merge | Eventual |
| Conflict | Last-writer-wins | Automatic |

---

## Configuration

```yaml
cognitive_memory:
  backend: "TurboMemory-Isolated"
  vector_dimensions: 4096
  encryption_at_rest: true
  context_ttl_seconds: 3600
  kv_cache_isolation: true
```

---

## See Also

- [Runtime Layer](/docs/runtime/index.md)
- [Deployment Profiles](/docs/deployment/profiles.md)
- [Security Model](/docs/security/threat-model.md)
