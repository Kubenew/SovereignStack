# RFC-0057: gRPC Alignment Streamer

| Field | Value |
|-------|-------|
| Status | Draft |
| Depends On | RFC-0056, RFC-0033 (MindSync) |
| Proto | `mind_sync.proto` |
| Service | `SovereignAlignmentService` |

## Overview

Extends the MindSync gRPC service with a `SovereignAlignmentService`
that streams alignment proofs between agents for real-time verification.

## Protocol

```protobuf
service SovereignAlignmentService {
  rpc StreamAlignmentProofs (stream ZkAlignmentProofMessage)
      returns (stream AlignmentVerificationResponse);
}
```

## Message Flow

1. Agent A sends `ZkAlignmentProofMessage` with action intent
2. Agent B verifies the proof against shared values
3. Returns `AlignmentVerificationResponse` with result
4. Both agents log via `values://` and `evidence://` URIs

## Server Implementation

See `ss-memory/src/grpc_server.rs` — `SovereignAlignmentService`
implementation.
