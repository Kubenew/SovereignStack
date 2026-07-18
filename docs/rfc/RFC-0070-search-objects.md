# RFC-0070: Search Objects

**Status:** Draft
**Layer:** Reasoning & Memory
**Depends on:** RFC-0001 (Sovereign Object Model), RFC-0006 (Reasoning Objects), RFC-0007 (Event Bus)
**Related:** RFC-0071 (Search Execution Protocol)

## Abstract

This RFC defines the `search://` URI scheme and the search graph object model for representing inference‑time search within SovereignStack. A search is modelled as a directed graph of nodes and edges, each addressable via `reason://` URIs, enabling auditable, replayable, and portable search across sovereign boundaries.

## Motivation

Modern AI agents rely on inference‑time search—MCTS, beam search, iterative retrieval—to improve answer quality. Without a standard representation, each agent hardcodes its own ad‑hoc logic, making it impossible to audit *how* a conclusion was reached, replay the search independently, or federate search across nodes. By making search an addressable, cryptographically verifiable graph, SovereignStack turns a black‑box process into a governable cognitive operation.

## Specification

### 1. URI Scheme

```
search://{agent-id}/{search-id}
```

- `agent-id` — the UAI of the agent that initiated the search.
- `search-id` — a unique identifier (UUID or content-hash) for this search episode.

Resolution returns a search state object describing the graph, verification, and answer.

### 2. Search Graph (not tree)

Searches are modelled as a **directed graph** (not a tree). Nodes represent cognitive states; edges represent transitions. This accomodates MCTS (tree), beam search (DAG), graph-of-thought (cyclic), and iterative retrieval (graph with back-edges).

#### 2.1 Search State Object

```json
{
  "$schema": "https://sovereignstack.org/schemas/search-state-v1.json",
  "id": "search://agent-42/550e8400-e29b-41d4-a716-446655440000",
  "query": "What are the latest SOTA approaches to chain-of-thought reasoning?",
  "strategy": "urn:ss-search:mcts",
  "parameters": {
    "max_iterations": 1000,
    "exploration_constant": 1.414,
    "max_depth": 10
  },
  "graph": {
    "root": "reason://agent-42/node-0",
    "nodes": {
      "reason://agent-42/node-0": {
        "action": "initial_query",
        "content": "what is SOTA chain-of-thought 2025?",
        "assumptions": ["user_query_is_well_formed"],
        "constraints": ["max_tokens_4096"],
        "confidence": 0.5,
        "cost": 0.001,
        "latency_ms": 120,
        "energy_mj": 0.05,
        "evidence": [
          "knowledge://arxiv/2501.12345",
          "artifact://search-engine/result-01"
        ],
        "visits": 45,
        "value": 0.78
      },
      "reason://agent-42/node-1": { "...": "..." }
    },
    "edges": [
      { "from": "reason://agent-42/node-0", "to": "reason://agent-42/node-1", "label": "refine" },
      { "from": "reason://agent-42/node-0", "to": "reason://agent-42/node-2", "label": "expand" }
    ]
  },
  "verification": {
    "method": "self-consistency-check",
    "score": 0.92,
    "evidence_chain": ["reason://verification-abc"],
    "verifier": "agent://validator-1",
    "signature": "ed25519:..."
  },
  "final_answer": {
    "path": ["reason://agent-42/node-0", "reason://agent-42/node-2", "reason://agent-42/node-5"],
    "content": "Recent advances include ...",
    "confidence": 0.92,
    "signature": "ed25519:..."
  },
  "provenance": "chain://..."
}
```

#### 2.2 Field Semantics

| Field | Description |
|-------|-------------|
| `query` | The original task or question. |
| `strategy` | Registered search strategy URN (see §3). |
| `parameters` | Strategy-specific settings. |
| `graph.nodes` | Map of `reason://` URIs to node objects. Nodes are stored as independent `reason://` resources, not embedded blobs, enabling distributed storage and partial replay. |
| `graph.nodes[*].evidence` | URIs to knowledge objects or artifacts that contributed to this node's evaluation. |
| `graph.nodes[*].assumptions` | Explicit assumptions made at this node. |
| `graph.nodes[*].constraints` | Resource or policy constraints active at this node. |
| `graph.nodes[*].cost` | Estimated compute cost for this node. |
| `graph.nodes[*].latency_ms` | Observed latency for this node. |
| `graph.nodes[*].energy_mj` | Estimated energy for this node. |
| `graph.nodes[*].confidence` | Self-assessed confidence [0,1]. |
| `graph.edges` | Array of directed edges connecting nodes. |
| `verification` | Signed assessment of overall search quality. |
| `final_answer` | Selected answer with winning path and confidence. |

### 3. Search Strategies

The `strategy` field MUST be a URN from the `urn:ss-search:` namespace:

| URN | Description |
|-----|-------------|
| `urn:ss-search:mcts` | Monte Carlo Tree Search |
| `urn:ss-search:beam` | Beam search with configurable width |
| `urn:ss-search:dfs` | Depth-first search |
| `urn:ss-search:bfs` | Breadth-first search |
| `urn:ss-search:astar` | A* search |
| `urn:ss-search:rag` | Retrieval-augmented generation |
| `urn:ss-search:tree-of-thought` | Tree-of-Thought prompting |
| `urn:ss-search:graph-of-thought` | Graph-of-Thought exploration |
| `urn:ss-search:react` | Reason-and-Act loop |
| `urn:ss-search:reflection` | Self-reflection cycle |
| `urn:ss-search:planner` | Symbolic planning |
| `urn:ss-search:custom` | User-defined; name specified in `parameters.strategy_name` |

New strategies can be registered through the RFC process by reserving a URN.

### 4. Node Storage as reason:// URIs

Search graph nodes MUST be stored as independent `reason://` resources rather than embedded blobs inside the search object. This enables:

- **Scale:** graphs with millions of nodes without bloating the search object
- **Partial replay:** replay only a subtree by resolving specific `reason://` URIs
- **Provenance:** each node has its own provenance chain in `ss-provenance`
- **Distributed storage:** nodes may live on different sovereign nodes

### 5. Event Stream

Every operation on a search graph MUST emit an event to the event bus (`ss-eventbus`):

| Event | Description |
|-------|-------------|
| `search.created` | Search episode initiated |
| `search.node.expanded` | New node added to graph |
| `search.node.evaluated` | Node received a value/confidence update |
| `search.edge.created` | Directed edge added between nodes |
| `search.verification.completed` | Verification step finished |
| `search.finalized` | Final answer selected and signed |

The complete event sequence MUST be replayable to reconstruct the search graph at any point using `replay://`.

### 6. Security Considerations

- **Data Poisoning:** Agents should verify evidence sources cryptographically before incorporating them. The verification block can cross-reference independent validators.
- **Infinite Loops:** Strategies allowing unbounded growth (e.g., MCTS without iteration limits) pose a DoS risk. Implementations MUST enforce parameter bounds and allow `ss-policy` to terminate searches exceeding resource limits.
- **Information Leakage:** Search graphs may reveal sensitive data. Agents SHOULD apply jurisdiction policies (RFC-0021) when transmitting search state across federation boundaries.
- **Node Hijacking:** All node mutations MUST be signed by the responsible agent identity. A guardian node (`safeguard://`) can monitor for anomalous branching patterns.

### 7. Conformance

To claim conformance with this RFC, an implementation MUST:

1. Represent searches using the `search://` URI scheme and the defined graph object.
2. Store search nodes as independent `reason://` resources.
3. Emit all `search.*` events to a compliant event bus.
4. Support at least one search strategy from the `urn:ss-search:` namespace.
5. Provide a `replay://` endpoint that reconstructs the search graph from the event log.
6. Advertise `capability://search-inference` when applicable.

### 8. References

- RFC-0001: Sovereign Object Model
- RFC-0006: Reasoning Objects
- RFC-0007: Event Bus
- RFC-0071: Search Execution Protocol
