# 09 — Sovereign Intelligence Protocol (SIP)

**Layer:** Infrastructure → All
**Status:** Draft
**Source:** `ss-sip/`

## Overview

SIP is the universal wire protocol for all SovereignStack communication. It is to intelligence networks what TCP/IP is to data networks.

## Protocol Convergence

All domain-specific protocols converge into SIP:

```
SEP (Session Exchange)      ─┐
SDP (Session Discovery)     ─┤
SAP (Session Artifact)      ─┼─→  SIP
SMP (Session Memory)        ─┤
AGP (Autonomous Governance) ─┘
```

## Message Format

```json
{
  "sip_version": "1.0",
  "message_id": "msg:a1b2c3d4",
  "type": "request",
  "protocol": "sap",
  "sender": "agent://sender",
  "target": "agent://receiver",
  "payload": {},
  "capability": "capability://required",
  "timestamp": "2026-05-31T12:00:00Z",
  "signature": "sig:abc..."
}
```

## Transport

- Default: WebSocket (WSS) for bidirectional streaming
- Fallback: HTTPS for request/response
- Future: QUIC for low-latency

## Protocol Operations

| Operation | Description |
|-----------|-------------|
| `handshake` | Establish connection, exchange capabilities |
| `ping/pong` | Keepalive |
| `capability_exchange` | Advertise supported protocols |
| `message` | Send/receive protocol-specific messages |
| `subscribe` | Subscribe to event stream |
| `resolve` | URI resolution request |

## URI Resolution over SIP

```
SIP Request: RESOLVE agent://target-agent
SIP Response: {
  "uri": "agent://target-agent",
  "resolved_by": "node://resolver",
  "object": { ... agent object ... }
}
```
