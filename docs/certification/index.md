# OASA Certification Program

The OASA Certification Program provides formal certification levels for SovereignStack Nodes, Runtimes, and Federations. Certified entities are registered in a public registry with cryptographically signed attestations.

---

## Programs

### Certified Node

| Level | Requirements |
|---|---|
| **L1** | Data ingestion, deterministic extraction, content hashing |
| **L2** | Memory isolation, local KV, vector store, encryption at rest |
| **L3** | Runtime AWQ/INT4, TEE-gated execution, rate-limited inference |

### Certified Runtime

| Level | Requirements |
|---|---|
| **L1** | OASA-compatible API, compliance lock, audit log |
| **L2** | JWT auth, OPA policy engine, Merkle-tree audit, hardware binding |
| **L3** | TEE attestation, enclave-gated inference, runtime shield |

### Certified Federation

| Level | Requirements |
|---|---|
| **L1** | CRDT sync, event log, node identity |
| **L2** | Jurisdictional gating, signed events, peer health tracking |
| **L3** | Weight federation, cross-node inference, audit provenance |

---

## Certification Registry API

The certification service runs on port **8086** by default.

### View programs

```bash
# List all certification programs
curl http://localhost:8086/certification/programs

# Get program details
curl http://localhost:8086/certification/programs/node
curl http://localhost:8086/certification/programs/runtime
curl http://localhost:8086/certification/programs/federation
```

### Register a certified entity

```bash
curl -X POST http://localhost:8086/certification/registry \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "My Sovereign Node",
    "subject_version": "1.0.0",
    "program": "node",
    "level": "L2",
    "contact": "admin@example.com"
  }'
```

### Query the registry

```bash
# All entries
curl http://localhost:8086/certification/registry

# Filter by program
curl "http://localhost:8086/certification/registry?program=runtime"

# Filter by level
curl "http://localhost:8086/certification/registry?level=L3"

# Filter by status
curl "http://localhost:8086/certification/registry?status=active"
```

### Update certification status

```bash
curl -X POST http://localhost:8086/certification/registry/{entry_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status": "revoked"}'
```

Valid statuses: `active`, `expired`, `revoked`, `suspended`

### Verify a certification

```bash
# Verify by registry ID
curl http://localhost:8086/certification/verify/{entry_id}
```

Returns:
```json
{
  "valid": true,
  "status": "active",
  "expired": false,
  "program": "node",
  "level": "L2",
  "subject_name": "My Sovereign Node"
}
```

---

## CLI Tools

### Issue a certification

```bash
# Generate a compliance report first
python -m pytest tests/conformance/ -v --report=json > report.json

# Issue certification
python tools/issue_certification.py \
  --report report.json \
  --level L2 \
  --subject-name "My Node" \
  --subject-type node \
  --output attestation.json
```

### Verify a certification

```bash
# Verify local attestation file
python tools/verify_certification.py --attestation attestation.json

# Verify against the registry
python tools/verify_certification.py --registry-id {entry_id}

# Both
python tools/verify_certification.py \
  --attestation attestation.json \
  --registry-id {entry_id}
```

---

## Certification Lifecycle

```
                   ┌─────────────┐
                   │  Conformance │
                   │    Tests     │
                   └──────┬──────┘
                          │ pass
                          ▼
                   ┌─────────────┐
                   │    Issue    │
                   │ Certificate │
                   └──────┬──────┘
                          │
                          ▼
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Active  │──►│ Expired  │   │ Revoked  │
    └──────────┘   └──────────┘   └──────────┘
          │
          ▼
    ┌──────────┐
    │Suspended │
    └──────────┘
```

- **Active** — Certification is valid and verifiable
- **Expired** — 365-day validity period has passed
- **Revoked** — Certification was invalidated (security issue, non-compliance)
- **Suspended** — Temporarily invalid pending review

---

## Integration with Conformance Tests

```bash
# Run OASA L2 conformance suite
python -m pytest tests/conformance/ -v

# Issue certification from results
python tools/issue_certification.py \
  --report reports/l2-conformance.json \
  --level L2 \
  --subject-name "My Node" \
  --subject-type node

# Register in the certification registry
# (manually upload attestation.json or use CI)
```

---

## Badges

Certified entities can display OASA badges:

| Level | Badge |
|---|---|
| **L1** | ![OASA L1](https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-l1.svg) |
| **L2** | ![OASA L2](https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-l2.svg) |
| **L3** | ![OASA L3](https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-l3.svg) |

---

## See Also

- [Services: certification_service.py](/services/certification_service.py)
- [Tool: issue_certification.py](/tools/issue_certification.py)
- [Tool: verify_certification.py](/tools/verify_certification.py)
- [Schema: oasa-certification.schema.json](/schemas/certification/oasa-certification.schema.json)
- [Conformance Tests](/tests/conformance/)
- [OASA Specification](/OASA.md)
