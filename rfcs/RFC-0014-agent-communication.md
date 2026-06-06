# RFC-0014: Agent Communication Protocol

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0003

## Summary

Defines the message format, delivery semantics, and routing rules for agent-to-agent communication within and across fabrics.

## Specification

### Message Envelope

```json
{
  "id": "msg://zcube-a/abc123",
  "from": "agent://researcher-1",
  "to": "agent://validator-7",
  "type": "request",
  "protocol": "sap",
  "payload": {"action": "verify", "target": "knowledge://physics/newton/v2"},
  "ttl_secs": 60,
  "reply_to": "msg://zcube-a/abc123",
  "signature": "ed25519:base64url..."
}
```

### Delivery Guarantees

- **At-least-once** for all messages (idempotent handlers)
- **Exactly-once** for financial/contract operations
- Ordered delivery within a session

### Routing

Messages are routed through the event bus (RFC-0007). Cross-fabric messages use federation routing (RFC-0008/RFC-0035).
