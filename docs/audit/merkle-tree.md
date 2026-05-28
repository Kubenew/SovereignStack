# Merkle Tree Audit Chain

SovereignStack implements an **append-only Merkle tree** over all audit events, providing tamper-evident logging for compliance (GDPR Art. 32, HIPAA 164.312(b), SOC 2 CC6).

Every API request, response, auth failure, and policy violation is hashed into a SHA-256 Merkle tree. The current root hash serves as a cryptographic fingerprint of the entire audit log.

---

## Architecture

```
                     Merkle Root (sha256)
                    /                    \
              h01                         h23
            /    \                      /    \
         h0      h1                 h2        h3
         |        |                  |         |
    Event #0  Event #1          Event #2   Event #3
    (auth)    (request)         (response) (compliance)
```

- **Leaf:** `SHA-256(JSON(event, sort_keys=True))`
- **Internal node:** `SHA-256(left_hash + right_hash)`
- **Odd leaves** are propagated up one level (balanced binary tree)
- All operations are **append-only** — past events cannot be modified without changing the root

---

## API Endpoints

### `GET /audit/root`

Returns the current Merkle tree root and size.

```bash
curl http://localhost:8080/audit/root
```

```json
{
  "root": "bdd30156f25b0a2ec7e3308a09db29c62f36f87f3f2e252244d96f70bdd10058",
  "size": 42
}
```

### `GET /audit/proof/{index}`

Returns the Merkle proof for a specific event index, along with the event and current root.

```bash
curl http://localhost:8080/audit/proof/0
```

```json
{
  "index": 0,
  "event": {"type": "request", "model": "Qwen/Qwen2.5-7B-Instruct", ...},
  "proof": [
    {"position": "right", "hash": "41b1c5e1e4398388f640b0a5804a2dc4..."},
    {"position": "right", "hash": "e59356a35bda8c6e240fb9f1f7ecc474d..."}
  ],
  "root": "bdd30156f25b0a2ec7e3308a09db29c62f36f87f3f2e252244d96f70bdd10058"
}
```

### `GET /audit/events`

Lists audit events with pagination.

```bash
curl "http://localhost:8080/audit/events?limit=5&offset=0"
```

---

## Verification

### Using the CLI tool

```bash
# Show current root and tree size
python tools/verify_audit.py

# Get Merkle proof for event at index 0
python tools/verify_audit.py --index 0

# Verify full tree integrity (rebuilds tree from events)
python tools/verify_audit.py --verify

# Export all leaves and proofs for external auditing
python tools/verify_audit.py --export-proofs
```

### Manual verification

```python
from services.merkle_audit import MerkleTree, _hash_event

# Build tree from audit events
tree = MerkleTree.load()

# Get event and proof
index = 0
event = tree.get_event(index)
proof = tree.get_proof(index)

# Verify
assert tree.verify_event(event, proof, tree.root)
```

---

## Persistence

The Merkle tree is persisted to `data/merkle_tree.json` after every append. This file contains:

```json
{
  "root": "bdd30156f25b0a2ec7e3308a09db29c62f36f87f3f2e252244d96f70bdd10058",
  "size": 42,
  "events": [
    {"type": "request", "ts": "2026-05-28T12:00:00Z", ...},
    ...
  ]
}
```

On service restart, the tree is loaded from disk and new events are appended.

---

## Security Properties

| Property | Guarantee |
|---|---|
| **Append-only** | Past events cannot be inserted, deleted, or reordered |
| **Tamper-evident** | Any modification changes the root hash |
| **Compact proof** | Proof size = O(log n) for n events |
| **Independent verification** | Any party can verify a proof against the published root |

---

## Compliance Mapping

| Framework | Requirement | How Merkle Tree Fulfills It |
|---|---|---|
| **GDPR Art. 32** | Security of processing | Tamper-evident audit trail |
| **HIPAA 164.312(b)** | Audit controls | Cryptographic audit log integrity |
| **SOC 2 CC6** | Logical access | Append-only immutable log |
| **OASA L2** | Verified compliance | Merkle root published + verifiable |

---

## See Also

- [Services: merkle_audit.py](/services/merkle_audit.py)
- [Tool: verify_audit.py](/tools/verify_audit.py)
- [Compliance Framework](/docs/compliance/index.md)
- [Security Overview](/docs/security/index.md)
