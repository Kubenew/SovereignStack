# RFC-0005: Knowledge Objects

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee
**Supersedes:** RFC-0006-knowledge-objects

## Abstract

Defines Knowledge Objects — versioned, verifiable, content-addressed units of information that form the long-term memory of the SovereignStack network. Unlike documents (opaque blobs) or vectors (numeric embeddings), Knowledge Objects are structured, self-describing, and cryptographically anchored.

## Motivation

Current AI ecosystems store documents, vectors, and embeddings. SovereignStack standardizes a richer abstraction: Knowledge Objects with built-in evidence, reasoning traces, trust assessments, and provenance — enabling machines to reason about what they know and why they know it.

## Specification

### Knowledge Object

```json
{
  "id": "knowledge://science/physics/newton/v1",
  "type": "knowledge",
  "owner": "org://science",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:00:00Z",
  "signature": "sig:abc...",
  "provenance": [
    {"action": "derived", "source": "knowledge://experiment/001", "timestamp": "2026-05-31T11:00:00Z"}
  ],
  "knowledge": {
    "title": "Newton's Second Law",
    "summary": "F = ma",
    "domain": "physics",
    "claims": [
      {"statement": "Force equals mass times acceleration", "confidence": 0.99, "evidence": ["evidence://experiment-001"]}
    ],
    "evidence": [
      {
        "id": "evidence://experiment-001",
        "type": "experimental",
        "description": "Controlled laboratory measurement",
        "source": "artifact://paper-001",
        "reproducibility": "high"
      }
    ],
    "reasoning": [
      {
        "id": "reason://deduction-001",
        "type": "deductive",
        "description": "Derived from conservation of momentum",
        "premises": ["knowledge://momentum-conservation"],
        "conclusion": "knowledge://newton-second-law"
      }
    ],
    "trust": {
      "score": 95,
      "verifications": ["verification://peer-review-001"],
      "certifications": ["certification://scientific-consensus"]
    },
    "related": [
      {"relation": "generalizes", "target": "knowledge://mechanics"},
      {"relation": "applied_by", "target": "capability://physics-simulator"}
    ],
    "tags": ["physics", "mechanics", "newton", "verified"]
  }
}
```

### Knowledge Types

| Type | Description | TTL |
|------|-------------|-----|
| `fact` | Verified truth claim | Indefinite |
| `hypothesis` | Proposed but unverified | Configurable |
| `observation` | Raw recorded data | Configurable |
| `derivation` | Logically derived from other knowledge | Depends on premises |
| `composite` | Aggregated from multiple sources | Configurable |

### Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Create | `POST /knowledge` | Store new knowledge |
| Read | `GET /knowledge/{uri}` | Retrieve by URI or content hash |
| Update | `PUT /knowledge/{uri}` | New version with provenance |
| Delete | `DELETE /knowledge/{uri}` | Tombstone (never truly deleted) |
| Merge | `POST /knowledge/merge` | Combine two knowledge objects |
| Diff | `POST /knowledge/diff` | Compute semantic diff |
| Query | `POST /knowledge/query` | Search by domain, tags, claims |

### Content Addressing

Knowledge content is addressed by SHA-256 hash:

```
knowledge://sha256:a1b2c3d4...
```

Updated content gets a new URI. The `provenance` array links versions.

### Trust Model Integration

Every Knowledge Object carries a trust assessment (RFC-0003):

- **score**: 0–100 aggregated trust
- **verifications**: references to third-party verifications
- **certifications**: references to formal certifications

Agents can filter knowledge by minimum trust threshold.

## Security Considerations

- Content-addressed URIs prevent undetected modification
- Knowledge claims require supporting evidence
- Trust score prevents propagation of unverified information
- Provenance chain enables full audit of knowledge derivation

## Reference Implementation

- `ss-kas` crate: knowledge addressing and storage
- Conformance tests: planned in `conformance/tests/kap/`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
