# RFC-0048: Federation Mesh Protocol

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `mesh://` |
| Depends On | RFC-0010, RFC-0022 (libp2p Discovery) |

## Overview

The `mesh://` URI scheme enables inter-fabric federation —
a sovereign agent in one fabric may discover and negotiate with
agents in another fabric.

## URI Scheme

`mesh://<fabric-id>[/<gateway>]`

Examples:
- `mesh://eu-fabric`
- `mesh://us-west-fabric/gateway-01`

## Discovery Flow

1. Fabric gateway announces `mesh://` URI via libp2p
2. Peer fabric resolves via DNS / DHT
3. Capability negotiation (RFC-0049) occurs before agent transfer
4. Lease acquired on remote fabric (RFC-0050)
