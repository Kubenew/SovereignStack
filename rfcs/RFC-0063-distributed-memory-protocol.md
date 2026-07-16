# RFC-0063: Distributed Memory Protocol (DMP)

**Status:** Draft | **Type:** Standard | **Created:** 2026-07-16 | **Depends On:** RFC-0006, RFC-0017, RFC-0060  
**Protocol ID:** DMP

## Abstract

Defines pointer-based memory exchange, content-addressed retrieval, delta synchronization, and the normative Memory Graph schema. DMP enables efficient sharing of massive cognitive contexts across distributed AI fabrics without full data serialization.

## Motivation

The biggest bottleneck in multi-model session interconnectivity is context window inflation — transferring thousands of tokens of prompt history back and forth. DMP implements context sharding and KV-cache offloading. Instead of passing full prompt histories, agents pass content-addressed pointers.

## Specification

### 1. Pointer-Based Exchange

Any memory object (`memory://`, `knowledge://`, `world://`, `checkpoint://`) MUST support pointer-based referencing.

When Agent A invokes Agent B with prior context, it passes a pointer:
```json
{
  "context": "kv://sha256:7a92ff01..."
}
```

Agent B's host node resolves this pointer via the Cognitive Router (RFC-0061). If the KV cache block exists locally (e.g., in HBM or shared NVLink memory), it is zero-copy mapped into the execution context.

### 2. Content-Addressed Retrieval

Memory objects are retrieved via content addressing:

```
GET mind://7a92ff01...
GET knowledge://abc12345...
```

The underlying resolution engine (Libp2p DHT, local index, etc.) locates the data blocks.

### 3. Delta Synchronization

For actively evolving sessions, context is synchronized via Deltas rather than full snapshots.

```json
{
  "type": "memory.delta",
  "base_hash": "sha256:abc...",
  "operations": [
    {"op": "append", "data": "New reasoning step..."}
  ],
  "new_hash": "sha256:def..."
}
```

### 4. Memory Graph Schema

The internal structure of a `mind://` follows a standardized graph:

```json
{
  "uri": "mind://enterprise",
  "quadrant": "cognitive",
  "nodes": {
    "goals": "knowledge://sha256:...",
    "beliefs": "knowledge://sha256:...",
    "knowledge_base": "knowledge://sha256:...",
    "sessions": "session://sha256:...",
    "policies": "policy://sha256:..."
  }
}
```

### 5. Semantic Caching

Results of expensive computations (e.g., MCTS reasoning paths) are cached as `reason://` objects. 

When a similar query is evaluated, the Cognitive Router can route to the cached `reason://` object if the semantic similarity exceeds a configured threshold, saving compute.

## Core Types

```rust
pub struct MemoryPointer {
    pub uri: SovereignUri,
    pub hash: String,
}

pub struct MemoryDelta {
    pub base_hash: String,
    pub operations: Vec<MemoryOp>,
    pub new_hash: String,
}

pub enum MemoryOp {
    Append(Vec<u8>),
    Delete(String), // Hash of segment to delete
}

pub struct MindGraph {
    pub uri: SovereignUri,
    pub goals: SovereignUri,
    pub beliefs: SovereignUri,
    pub knowledge_base: SovereignUri,
    pub sessions: SovereignUri,
    pub policies: SovereignUri,
}
```

## Security Considerations

- **Capability Verification**: Holding a pointer (e.g., `kv://sha256:...`) does NOT grant access to the underlying data. The node hosting the data MUST verify that the requesting session possesses a valid capability token for that object.
- **Cache Poisoning**: All cached objects MUST be cryptographically signed by their producer. Consumers MUST verify the signature against the producer's identity before integrating the knowledge.

## Conformance Impact

- Required for **SIRA-3** conformance
- Deprecates RFC-0017 (Sovereign Memory Protocol) in favor of pointer-based exchange
