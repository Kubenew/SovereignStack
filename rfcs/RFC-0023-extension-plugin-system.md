# RFC-0023: Extension & Plugin System

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0005

## Summary

Defines how third-party extensions and plugins are registered, sandboxed, versioned, and executed within a SovereignStack node.

## Specification

### Extension Manifest

```json
{
  "id": "ext://data-validator/v1.2.0",
  "name": "Data Validator",
  "type": "ingestion_filter",
  "api_version": "1.0",
  "permissions": ["capability://read-memory", "capability://write-audit"],
  "sandbox": "wasm",
  "entrypoint": "validate.wasm",
  "signature": "ed25519:base64url..."
}
```

### Sandbox Models

| Model | Isolation | Performance | Use Case |
|-------|-----------|-------------|----------|
| WASM | Process-level | High | Transformation filters |
| Native | OS-level | Highest | Performance-critical |

### Core Types

`ExtensionManifest`, `SandboxConfig`, `ExtensionRegistry`, `PluginInstance`
