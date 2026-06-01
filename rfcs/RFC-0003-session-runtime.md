# RFC-0003: Trust Graph

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the machine-readable trust model for SovereignStack — a graph of identity, verification, certification, reputation, and trust objects that enables automated trust evaluation across the network.

## Motivation

Trust in distributed intelligence networks cannot be boolean. Nodes, agents, and organizations need a multi-dimensional, machine-readable trust model that supports automated decision-making for routing, federation, capability delegation, and governance.

## Specification

### Trust Graph Objects

#### Identity

Every entity has a self-issued identity document:

```json
{
  "identity": "agent://research-1",
  "public_key": "ed25519:deadbeefcafebabe...",
  "algorithm": "Ed25519",
  "created_at": "2026-05-31T00:00:00Z",
  "expires_at": "2027-05-31T00:00:00Z",
  "metadata": {
    "name": "Research Agent 1",
    "jurisdiction": "EU"
  },
  "signature": "sig:abc123..."
}
```

#### Verification

Third-party verification that an identity is real:

```json
{
  "identity": "agent://research-1",
  "verification_id": "verification://001",
  "verifier": "node://trusted-verifier",
  "method": "keybase",
  "verified_at": "2026-05-31T00:00:00Z",
  "expires_at": "2027-05-31T00:00:00Z",
  "proof": "https://keybase.io/research-1/sig/abc123",
  "signature": "sig:def456..."
}
```

#### Certification

OASA certification level (L1–L3):

```json
{
  "identity": "node://infra-node",
  "certification_id": "certification://001",
  "level": "L2",
  "issued_by": "OASA Technical Steering Committee",
  "issued_at": "2026-05-31T00:00:00Z",
  "valid_until": "2027-05-31T00:00:00Z",
  "badge_url": "https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-l2.svg",
  "attestation": "sig:ghi789..."
}
```

#### Reputation

Network-consensus reputation score:

```json
{
  "identity": "agent://research-1",
  "reputation_id": "reputation://001",
  "total_interactions": 1500,
  "success_rate": 0.98,
  "avg_latency_ms": 42,
  "avg_accuracy": 0.95,
  "trust_score": 91,
  "last_updated": "2026-05-31T00:00:00Z",
  "computed_by": "node://reputation-oracle",
  "voters": ["node://voter-1", "node://voter-2", "node://voter-3"]
}
```

#### Trust

Computed trust assessment combining all of the above:

```json
{
  "identity": "agent://research-1",
  "assessed_by": "node://assessor",
  "verified": true,
  "verification_count": 3,
  "certification_level": null,
  "trust_score": 91,
  "confidence": 0.85,
  "assessed_at": "2026-05-31T00:00:00Z",
  "expires_at": "2026-06-01T00:00:00Z",
  "signature": "sig:jkl012..."
}
```

### Trust Graph Structure

```
Identity ──── has ────► Verification
   │                      │
   │                      ▼
   ├── has ──────────► Certification
   │
   ├── has ──────────► Reputation ◄─── Consensus Votes
   │
   └── evaluated ────► Trust Assessment
```

### Trust Score Computation

Trust score (0–100) is computed as:

```
trust_score = (
    verification_weight * verification_bonus +
    certification_weight * certification_bonus +
    reputation_accuracy_weight * accuracy +
    reputation_reliability_weight * reliability
)
```

Default weights are TSC-defined but can be overridden per node.

### Trust Usage

| Use Case | Threshold | Decision |
|----------|-----------|----------|
| Task routing | trust_score >= 70 | Route to agent |
| Federation | trust_score >= 80 | Allow replication |
| Capability delegation | trust_score >= 60 | Allow delegation |
| Certification | L2+ required | Access sensitive data |
| Governance | policy-defined | Enforce thresholds |

### Trust Graph API

```
GET /trust/identity/<uri>          — Get identity's trust assessment
GET /trust/verifications/<uri>     — List verifications
GET /trust/certifications/<uri>    — List certifications
GET /trust/reputation/<uri>        — Get reputation score
POST /trust/verify                  — Submit new verification
POST /trust/report-interaction     — Report interaction outcome
```

## Security Considerations

- Trust assessments expire and must be refreshed
- Verification requires cryptographic proof
- Reputation can be gamed; mitigation via multi-voter consensus
- Trust thresholds are node-local policy decisions
- Centralized reputation oracles are discouraged

## Reference Implementation

- `ss-trust` crate: graph storage, computation, API
- `ss-kernel::policy` — policy engine evaluates trust thresholds

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
