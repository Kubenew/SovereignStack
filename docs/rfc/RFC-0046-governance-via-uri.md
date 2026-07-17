# RFC-0046: Governance via URI

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `governance://` |
| Depends On | RFC-0010, RFC-0045 |

## Overview

Governance decisions are modeled as first-class URI resources,
enabling implementation-independent consensus, audit trails, and
delegation across organizational boundaries.

## URI Scheme

`governance://<org>/<proposal-id>`

Examples:
- `governance://acme-corp/proposal-88`
- `governance://sovereignstack/decision-2026-01`

## Resolution Flow

1. Proposal created via `governance://` URI
2. Agents vote/consent using `values://` alignment check
3. Decision recorded as immutable artifact
4. All agents reconcile via MindSync
