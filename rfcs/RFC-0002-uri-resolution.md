# RFC-0002: Sovereign URI Standard

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines the URI scheme registry, formal ABNF grammar, resolution mechanism, and versioning conventions for all SovereignStack objects.

## Motivation

Following Principle 4 — Address Everything, every object must have a globally unique, resolvable URI. A standard URI format enables interoperability, federation, and offline-first resolution.

## Specification

### URI Structure

```
URI = scheme ":" hier-part [ "?" query ] [ "#" fragment ]
scheme = "agent" / "session" / "memory" / "knowledge"
       / "reason" / "artifact" / "workflow" / "capability"
       / "policy" / "node" / "org"
hier-part = "//" authority path-abempty
authority = [ identity "@" ] host [ ":" port ]
identity = 1*( unreserved / pct-encoded )
host = IP-literal / IPv4address / reg-name
path-abempty = *( "/" segment )
segment = *pchar
query = *( pchar / "/" / "?" )
fragment = *( pchar / "/" / "?" )
```

### Formal ABNF

```abnf
URI = scheme ":" hier-part [ "?" query ] [ "#" fragment ]

scheme = "agent" / "session" / "memory" / "knowledge"
       / "reason" / "artifact" / "workflow" / "capability"
       / "policy" / "node" / "org"

hier-part = "//" authority path-abempty
          / path-absolute
          / path-rootless
          / path-empty

authority = [ userinfo "@" ] host [ ":" port ]
userinfo = *( unreserved / pct-encoded / sub-delims / ":" )
host = IP-literal / IPv4address / reg-name
port = 1*DIGIT

path-abempty = *( "/" segment )
path-absolute = "/" [ segment-nz *( "/" segment ) ]
path-rootless = segment-nz *( "/" segment )
path-empty = ""

segment = *pchar
segment-nz = 1*pchar
pchar = unreserved / pct-encoded / sub-delims / ":" / "@"

query = *( pchar / "/" / "?" )
fragment = *( pchar / "/" / "?" )

unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~"
pct-encoded = "%" HEXDIG HEXDIG
sub-delims = "!" / "$" / "&" / "'" / "(" / ")" / "*" / "+" / "," / ";" / "="
```

### Registered Schemes

| Scheme | Authority | Description | Example |
|--------|-----------|-------------|---------|
| `agent` | agent-id | Agent identity | `agent://researcher-1` |
| `session` | session-id | Active session | `session://abc123` |
| `memory` | memory-id | Memory object | `memory://mem-001` |
| `knowledge` | content-hash | Knowledge object | `knowledge://sha256:abc123` |
| `reason` | reason-trace | Reasoning chain | `reason://decision-42` |
| `artifact` | artifact-hash | Produced artifact | `artifact://sha256:def456` |
| `workflow` | workflow-name | Workflow definition | `workflow://contract-analysis` |
| `capability` | capability-name | Permission token | `capability://delegated:read:memory://x` |
| `policy` | policy-name | Governance rule | `policy://gdpr-data-residency` |
| `node` | node-id | Network node | `node://homelab-1` |
| `org` | org-name | Organization | `org://acme-corp` |

### Versioning Convention

Knowledge and policy objects support versioned URIs:

```abnf
versioned-uri = scheme "://" authority "/" path [ "/v" version ]
version = 1*DIGIT "." 1*DIGIT "." 1*DIGIT
```

Examples:
- `knowledge://physics/newton/v1.0.0`
- `policy://gdpr-eu/v2.1.0`
- `workflow://data-pipeline/v3.0.0`

When no version is specified, the resolver returns the **latest** version.

### Resolution Rules

1. **Local Resolution** — Check local node registry first (offline-first)
2. **Cache** — Check LRU cache with configurable TTL
3. **Trusted Peers** — Query configured federation peers
4. **Federation Discovery** — Broadcast query to network (if policy allows)

### Resolution Response

```json
{
  "uri": "agent://researcher-1",
  "object_type": "agent",
  "resolved_by": "node://resolver-node",
  "resolved_at": "2026-05-31T12:00:00Z",
  "object": { ... },
  "provenance": ["node://cache-hit", "node://origin-node"]
}
```

### Error Responses

| Code | Meaning | When |
|------|---------|------|
| 404 | Not Found | Object does not exist |
| 403 | Forbidden | Capability check failed |
| 410 | Gone | Object tombstoned |
| 504 | Gateway Timeout | Federation timeout |

### URI Normalization

- All URIs are case-insensitive and normalized to lowercase
- Query parameters are preserved in canonical (sorted) order
- Fragments are resolved server-side by default
- Percent-encoding is normalized (uppercase hex digits)

## Security Considerations

- URI resolution requires appropriate capability
- Resolution chains must be verifiable via provenance
- Federation resolution is opt-in per policy
- Cache poisoning is mitigated by signature verification on resolved objects

## Reference Implementation

- `ss-kernel::resolver::UriResolver` — kernel resolver trait
- `ss-kernel::resolver::UriResolverImpl` — default implementation

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-31 | Initial specification |
