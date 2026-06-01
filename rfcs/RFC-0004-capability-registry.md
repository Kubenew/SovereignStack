# RFC-0004: Capability Registry

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee
**Supersedes:** RFC-0004-capability-system

## Abstract

Defines the Capability Registry — a discoverable, machine-readable catalog of capabilities that agents, nodes, and services can advertise, query, and bind to. The capability is the fundamental unit of service discovery in SovereignStack, analogous to DNS records for the intelligence network.

## Motivation

Without a standard capability model, agents cannot discover what other agents can do. The capability registry fills the role of DNS + service discovery + package registry for intelligence systems.

## Specification

### Capability Object

```json
{
  "id": "capability://legal-review",
  "type": "capability",
  "owner": "agent://legal-a",
  "version": "1.0.0",
  "created": "2026-05-31T12:00:00Z",
  "updated": "2026-05-31T12:00:00Z",
  "signature": "sig:abc...",
  "provenance": [],
  "capability": {
    "provider": "agent://legal-a",
    "display_name": "GDPR Legal Review",
    "description": "Reviews documents for GDPR compliance",
    "inputs": [
      {"name": "document", "type": "artifact://", "required": true},
      {"name": "jurisdiction", "type": "string", "required": false}
    ],
    "outputs": [
      {"name": "assessment", "type": "knowledge://", "required": true},
      {"name": "risk_score", "type": "float", "required": false}
    ],
    "trust_required": 70,
    "pricing": {"model": "per_request", "amount": 0},
    "tags": ["legal", "gdpr", "compliance"]
  }
}
```

### Registry Operations

| Operation | Method | Description |
|-----------|--------|-------------|
| Register | `PUT /capabilities` | Advertise a capability |
| Query | `POST /capabilities/query` | Find capabilities by criteria |
| Resolve | `GET /capabilities/{id}` | Get capability details |
| Bind | `POST /capabilities/{id}/bind` | Establish a binding |
| Unbind | `DELETE /capabilities/{id}/bind` | Remove a binding |
| Revoke | `DELETE /capabilities/{id}` | Remove a capability |

### Query Language

```json
{
  "query": {
    "tags": ["legal", "gdpr"],
    "input_types": ["artifact://"],
    "trust_min": 70,
    "jurisdiction": "EU",
    "max_results": 10
  }
}
```

### Binding Object

A binding represents an active use of a capability:

```json
{
  "id": "binding://legal-review-for-doc-123",
  "capability": "capability://legal-review",
  "consumer": "agent://client-agent",
  "provider": "agent://legal-a",
  "status": "active",
  "created": "2026-05-31T12:00:00Z",
  "expires": "2026-06-01T12:00:00Z",
  "terms": {"max_calls": 100}
}
```

### Capability Types Registry

| Type | Prefix | Example |
|------|--------|---------|
| Reasoning | `capability://reason/` | `capability://reason/legal-analysis` |
| Knowledge | `capability://knowledge/` | `capability://knowledge/gdpr-search` |
| Memory | `capability://memory/` | `capability://memory/session-store` |
| Compute | `capability://compute/` | `capability://compute/model-inference` |
| Communication | `capability://comm/` | `capability://comm/message-relay` |
| Federation | `capability://fed/` | `capability://fed/discovery` |
| Governance | `capability://gov/` | `capability://gov/policy-eval` |

## Security Considerations

- Registration requires the provider's cryptographic signature
- Capabilities are revocable at any time
- Bindings expire by default (max 24h)
- Trust score gates capability discovery
- Registry entries are cached with TTL

## Reference Implementation

- `ss-capability` crate: registry, query engine, binding management
- Conformance tests: `conformance/tests/sip/test_sip.py` (capability_exchange)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
