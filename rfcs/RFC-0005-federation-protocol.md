# RFC-0005: Federation Protocol

**Status:** Draft
**Type:** Standard
**Created:** 2026-05-31
**Authors:** SovereignStack Standards Committee

## Abstract

Defines how SovereignStack nodes discover each other, establish trust, and exchange objects across administrative boundaries.

## Motivation

A distributed intelligence network requires nodes to cooperate while preserving sovereignty.

## Specification

### Discovery

- Nodes announce presence via configurable discovery mechanisms
- Supported: mDNS (local), DNS SRV (domain), Peer Exchange (bootstrap list)
- Discovery responses include node capability matrix

### Trust Establishment

1. Node A requests introduction
2. Node B presents its identity certificate
3. Node A verifies certificate chain
4. Optional: mutual capability exchange
5. Trust established for configurable duration

### Object Exchange

- Objects are requested via URI resolution (RFC-0002)
- Objects are transferred with provenance chain
- Transfers are encrypted end-to-end
- Receipt is acknowledged cryptographically

### Federation Policy

Each node defines a federation policy:

```json
{
  "federation_enabled": true,
  "trusted_nodes": ["node://...", ...],
  "max_delegation_depth": 3,
  "allowed_operations": ["resolve", "query", "subscribe"],
  "jurisdiction_filter": ["US", "EU", "JP"]
}
```

## Security Considerations

- Federation is opt-in per node
- Trust is ephemeral and re-verifiable
- Malicious peers are blacklisted locally

## Reference Implementation

- ss-federation crate: `crates/ss-federation/src/protocol.rs`
