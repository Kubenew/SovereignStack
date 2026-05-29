# Secure Weight Federation

SovereignStack Secure Weight Federation enables **sharded cross-node inference without any single node ever holding the full model weights**. Model weights are split into encrypted shards distributed across multiple federation nodes. Inference requests are routed through the shard chain; each node computes its forward pass and passes only activations (never weights) to the next node.

---

## Architecture

```
Client Request
     |
     v
Weight Federation Coordinator  (port 8087)
     |
     ├── Shard Node A (shard 0, layers 1-4)    ← encrypted weights, never exposed
     ├── Shard Node B (shard 1, layers 5-8)     ← encrypted weights, never exposed
     └── Shard Node C (shard 2, layers 9-12)    ← encrypted weights, never exposed
     
     Each node:
       - Stores weights encrypted with AES-256-GCM (Fernet)
       - Receives activations from previous shard
       - Computes forward pass (matrix multiply)
       - Returns activations to coordinator
       - NEVER exposes raw weights
```

**Security properties:**
- No single node holds the complete model
- Weights encrypted at rest (AES-256-GCM via `cryptography.fernet`)
- Inter-node communication over HTTP (mTLS/SPIFFE in production)
- Activations only — raw weights never leave the shard node

---

## API Endpoints

### Register a weight shard

```bash
curl -X POST http://localhost:8087/federation/weights/register \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "llama-7b",
    "model_version": "1.0.0",
    "shard_index": 0,
    "total_shards": 4,
    "layers": ["embed_tokens", "layer_0", "layer_1"],
    "node_endpoint": "http://shard-node-a:8087"
  }'
```

### Store encrypted weights on a node

```bash
curl -X POST http://localhost:8087/federation/weights/store \
  -H "Content-Type: application/json" \
  -d '{
    "shard_id": "llama-7b-v1.0.0-shard-0",
    "weights_b64": "<base64-encoded weight matrix JSON>",
    "metadata": {"source": "huggingface", "shard_index": 0}
  }'
```

Weights are encrypted with AES-256-GCM before being written to disk.

### Run sharded inference

```bash
curl -X POST http://localhost:8087/federation/weights/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "llama-7b",
    "model_version": "1.0.0",
    "input_data": [[0.1, 0.2, 0.3, ...]]
  }'
```

The coordinator:
1. Loads the weight topology from the manifest
2. Verifies all shards are healthy
3. Sends input to shard 0 → receives activations
4. Forwards activations to shard 1, then shard 2, etc.
5. Returns final output

### Shard info and health

```bash
# Get shard metadata
curl http://localhost:8087/federation/weights/shard/llama-7b-v1.0.0-shard-0

# Report shard health
curl -X POST http://localhost:8087/federation/weights/health \
  -H "Content-Type: application/json" \
  -d '{
    "node_endpoint": "http://shard-node-a:8087",
    "shard_id": "llama-7b-v1.0.0-shard-0",
    "healthy": true,
    "load": 0.45
  }'

# Federation status
curl http://localhost:8087/federation/weights/status
```

---

## CLI Tool

### Shard a model

```bash
# Split a .npy weight file into 4 shards
python tools/federate_weights.py shard \
  --model models/llama-7b/weights.npy \
  --output-dir ./shards/llama-7b \
  --num-shards 4 \
  --name llama-7b
```

Creates:
- `shards/llama-7b/manifest.json` — shard topology
- `shards/llama-7b/shard-0.json` through `shard-3.json` — weight shards (JSON matrices)

### Distribute shards to federation nodes

```bash
python tools/federate_weights.py distribute \
  --shard-dir ./shards/llama-7b \
  --nodes http://node-a:8087,http://node-b:8087,http://node-c:8087,http://node-d:8087
```

Each node receives:
1. A `POST /federation/weights/register` to announce its shard
2. A `POST /federation/weights/store` with encrypted weights

### Test sharded inference

```bash
python tools/federate_weights.py test \
  --model-name llama-7b \
  --nodes http://localhost:8087
```

Sends a random input vector through the full shard chain and prints the output.

---

## Topology Manifest

```json
{
  "shards": [
    {
      "shard_id": "llama-7b-v1.0.0-shard-0",
      "model_name": "llama-7b",
      "shard_index": 0,
      "total_shards": 4,
      "layers": ["embed_tokens"],
      "node_endpoint": "http://node-a:8087",
      "healthy": true,
      "stored": true,
      "checksum": "a1b2c3d4..."
    }
  ],
  "topology": {
    "llama-7b@v1.0.0": {
      "model_name": "llama-7b",
      "total_shards": 4,
      "created_at": "2026-05-28T..."
    }
  }
}
```

---

## Security Considerations

| Concern | Mitigation |
|---|---|
| Weight exfiltration | Encrypted at rest (AES-256-GCM); raw weights never transmitted |
| Shard node compromise | Attacker only sees one shard + activations, never full model |
| Replay attacks | Request IDs + session IDs per inference |
| Inter-node MITM | mTLS via SPIFFE/SPIRE (production); configurable per deployment |
| Tampered activations | Session-bound request IDs; activations never persist |

---

## Compliance Mapping

| Requirement | How Weight Federation Fulfills It |
|---|---|
| **OASA L3 Federation** | Sharded inference without weight sharing |
| **GDPR Art. 5(1)(c)** | Data minimisation — no node sees all weights |
| **HIPAA 164.312(a)(1)** | Unique user identification per shard access |
| **SOC 2 CC6.1** | Logical and physical access controls on weight data |
| **Confidential Computing** | Weight shards never leave TEE boundary of originating node |

---

## See Also

- [Services: weight_federation_service.py](/services/weight_federation_service.py)
- [Tool: federate_weights.py](/tools/federate_weights.py)
- [Federation Protocol (RFC 0004)](/rfcs/0004-federation-protocol.md)
- [Certification Program](/docs/certification/index.md)
- [Enterprise Platform](/docs/enterprise/index.md)
