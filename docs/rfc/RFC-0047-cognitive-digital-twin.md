# RFC-0047: Cognitive Digital Twin

| Field | Value |
|-------|-------|
| Status | Draft |
| URI Scheme | `twin://`, `identity://` |
| Depends On | RFC-0010, RFC-0045 |

## Overview

Every sovereign agent may have one or more digital twins — candidate
instances that mirror its behavior for validation, simulation, or
rollback purposes.

## URI Schemes

- `twin://<agent>/<candidate>` – twin instance
- `identity://<domain>/<entity>` – stable identity for agent or human

## Lifecycle

1. Identity provisioned via `identity://`
2. Twin spawned via `twin://`
3. Validation run; if passed, twin may be promoted
4. Original may rollback to twin state via `rollback://`
