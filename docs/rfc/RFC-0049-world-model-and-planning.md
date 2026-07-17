# RFC-0049: World Model & Execution Planning

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `world://`, `plan://`, `tool://` |
| Depends On | RFC-0010 |

## Overview

Agents reason about their environment via `world://` URIs, formulate
plans via `plan://`, and bind external tools via `tool://`.

## URI Schemes

- `world://<sim>/<environment>` – world model segment
- `plan://<agent>/<strategy-id>` – execution plan
- `tool://<agent>/<tool-name>` – tool binding

## Planning Cycle

1. Agent reads world state from `world://`
2. Generates candidate plans (`plan://`)
3. Simulates outcomes using `world://` model
4. Executes best plan using `tool://` bindings
5. Records reflection via `reflection://` (RFC-0045)
