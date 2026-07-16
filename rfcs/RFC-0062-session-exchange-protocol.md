# RFC-0062: Session Exchange Protocol (SXP)

**Status:** Draft | **Type:** Standard | **Created:** 2026-07-16 | **Depends On:** RFC-0003, RFC-0009, RFC-0060  
**Protocol ID:** SXP

## Abstract

Defines session isolation, cross-session exchange, and session migration semantics. Sessions in SovereignStack act as "Kubernetes namespaces for cognition," isolating memory, reasoning, capabilities, and policies. SXP defines how these isolated namespaces can securely share context and how they can be suspended, migrated, and restored.

## Motivation

In traditional conversational agent frameworks, all context lives in a single, ever-growing chat history. This leads to context window exhaustion, cross-contamination of ideas, and security vulnerabilities (prompt injection leaking across domains).

SXP isolates cognitive domains. A finance session and a legal session run independently. If they need to collaborate, they exchange specific, verified objects via SXP rather than merging their entire contexts.

## Specification

### 1. Session as a Cognitive Namespace

A session (`session://`) owns and isolates the following resources:

- **Memories** (`memory://`)
- **Reasoning Traces** (`reason://`)
- **Granted Capabilities** (`capability://`)
- **Active Policies** (`policy://`)
- **Tool Bindings** (`workflow://`)

Nothing leaks automatically between sessions.

### 2. Session Object Schema

```json
{
  "uri": "session://finance-q3-analysis",
  "type": "session",
  "quadrant": "operational",
  "parent_mind": "mind://enterprise",
  "state": "running",
  "isolation_level": "strict",
  "resources": {
    "memories": ["memory://sha256:abc...", "memory://sha256:def..."],
    "reasoning": ["reason://sha256:123..."],
    "capabilities": ["capability://db-read-finance"],
    "policies": ["policy://no-pii-export"]
  }
}
```

### 3. Cross-Session Exchange

To share context between sessions, an explicit exchange MUST occur.

1. **Request**: Session A requests an object from Session B.
2. **Policy Check**: Session B's active policies are evaluated.
3. **Grant**: Session B issues a read-only capability to Session A for the specific object.
4. **Exchange**: Session A accesses the object via a content-addressed pointer.

**Exchange Request:**
```json
{
  "action": "share",
  "source": "session://legal-review",
  "target": "session://finance-q3-analysis",
  "object": "knowledge://sha256:abc...",
  "reason": "Requires compliance verification"
}
```

### 4. Session Federation

Sessions can be federated across organizational boundaries using the `federation://` protocol (RFC-0004). This requires a **Cross-Jurisdiction Policy Check** (RFC-0021).

### 5. Session Checkpoint & Restore

Sessions can be suspended and restored. This involves creating a `checkpoint://` object that serializes the session state, active capabilities, and memory pointers.

**Checkpoint Object:**
```json
{
  "uri": "checkpoint://session-finance/timestamp",
  "session": "session://finance-q3-analysis",
  "state_hash": "sha256:...",
  "kv_cache_pointers": ["kv://sha256:..."],
  "signature": "ed25519:..."
}
```

### 6. Session Migration

Using checkpoints, a session can migrate across nodes or fabrics:

1. Suspend session on Node A (create checkpoint)
2. Transfer checkpoint magnet link to Node B
3. Node B resolves required KV caches and memory pointers
4. Restore session on Node B

## Core Types

```rust
pub struct SessionObject {
    pub uri: SovereignUri,
    pub parent_mind: SovereignUri,
    pub state: SessionState,
    pub isolation_level: IsolationLevel,
    pub resources: SessionResources,
}

pub enum IsolationLevel {
    Strict,
    Shared,
    Federated,
}

pub struct ExchangeRequest {
    pub source: SovereignUri,
    pub target: SovereignUri,
    pub object: SovereignUri,
    pub reason: String,
}

pub struct Checkpoint {
    pub uri: SovereignUri,
    pub session: SovereignUri,
    pub state_hash: String,
    pub kv_cache_pointers: Vec<String>,
}
```

## Security Considerations

- **Strict Isolation**: By default, no objects can be read or modified by other sessions.
- **Capability-Based Sharing**: All cross-session sharing relies on explicitly granted capability tokens.
- **Data Exfiltration**: Session policies MUST evaluate whether shared objects violate DLP (Data Loss Prevention) rules before granting access.

## Conformance Impact

- Required for **SIRA-2** conformance
- Replaces RFC-0025 (Session Migration)
