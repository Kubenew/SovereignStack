# RFC-0051: Explainability & Provenance

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `explanation://`, `summary://`, `timeline://` |
| Depends On | RFC-0010, RFC-0045 |

## Overview

Every cognitive decision SHOULD be traceable to an explanation.
The `explanation://`, `summary://`, and `timeline://` URI schemes
provide immutable audit trails for agent reasoning.

## URI Schemes

- `explanation://<reasoner>/<step>` – step-by-step explanation
- `summary://<session>/<digest>` – condensed summary
- `timeline://<agent>/<history>` – ordered event log

## Audit Use Cases

- Regulator requests `explanation://` for a KYC decision
- Operator inspects `summary://` of a trading session
- Debugger replays `timeline://` to reproduce a bug
