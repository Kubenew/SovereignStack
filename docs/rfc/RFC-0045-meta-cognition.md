# RFC-0045: Meta-Cognition Protocol

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `meta://`, `self://`, `reflection://`, `improvement://` |
| Depends On | RFC-0010 (URI Standard) |

## Overview

Define a protocol for AI self-modeling, reflection logging, and improvement tracking
using dedicated URI schemes and a gRPC service (`MetaCognitionService`).

## URI Schemes

- `meta://<agent>/<model>` – self-model state
- `self://<agent>/<aspect>` – introspective view
- `reflection://<agent>/<insight>` – logged reflection
- `improvement://<agent>/<patch>` – applied improvement

## gRPC Service

Defined in `ss-memory/proto/meta_cognition.proto`, supporting:
- `StreamSelfModel` – bidirectional delta streaming
- `LogReflection` – persist an insight
- `TrackImprovement` – record a validated patch

## Integration

The meta-cognition subsystem runs alongside MindSync and feeds into
the governance layer (RFC-0046) for oversight decisions.
