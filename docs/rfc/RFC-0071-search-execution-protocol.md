# RFC-0071: Search Execution Protocol

**Status:** Draft
**Layer:** Reasoning & Memory
**Depends on:** RFC-0070 (Search Objects)
**Related:** RFC-0057 (Meta-Cognition), RFC-0054 (Capability Negotiation)

## Abstract

This RFC defines the protocol lifecycle for executing, monitoring, and verifying inference‑time search across sovereign nodes. It specifies the request/response messages, capability advertisement, and state transitions that govern a search episode from initiation to finalization.

## Motivation

While RFC-0070 defines *what* a search object looks like, this RFC defines *how* search is initiated, expanded, evaluated, verified, and finalized across distributed agents. Separating the object model from the execution protocol follows the same pattern as HTTP (URI vs. methods) and enables independent evolution of storage and orchestration.

## Specification

### 1. Search Lifecycle

A search episode progresses through the following states:

```
Created → Planning → Expanding → Evaluating → Verifying → Finalized
                          ↑            |
                          └──── Retry ──┘
```

| State | Description |
|-------|-------------|
| **Created** | Search episode allocated. No nodes yet. |
| **Planning** | Strategy selected, parameters validated, resource budget allocated. |
| **Expanding** | New nodes and edges being added to the graph. |
| **Evaluating** | Nodes being scored for value, confidence, cost. |
| **Verifying** | Final verification step; independent validator may cross-check. |
| **Finalized** | Answer selected and signed. No further mutations allowed. |
| **Retry** | A failed evaluation may trigger re-expansion. |

### 2. Protocol Messages

#### 2.1 InitiateSearch

Initiator → Responder

```json
{
  "type": "search.initiate",
  "search_id": "uuid",
  "query": "string",
  "strategy": "urn:ss-search:mcts",
  "parameters": { "max_iterations": 1000 },
  "capability_offer": { "type": "capability://search-inference" },
  "budget": { "max_cost": 0.1, "max_latency_ms": 5000, "max_energy_mj": 10 },
  "safety_contract_uri": "contract://safety/search-42"
}
```

The responder MUST validate the safety contract before accepting.

#### 2.2 ExpandSearch

```json
{
  "type": "search.expand",
  "search_id": "uuid",
  "parent_node": "reason://agent-42/node-5",
  "actions": ["refine", "retrieve", "decompose"],
  "count": 3
}
```

#### 2.3 EvaluateNode

```json
{
  "type": "search.evaluate",
  "search_id": "uuid",
  "node": "reason://agent-42/node-7",
  "value": 0.85,
  "confidence": 0.72,
  "cost": 0.002,
  "latency_ms": 200,
  "energy_mj": 0.08,
  "evidence": ["knowledge://arxiv/2501.12345"]
}
```

#### 2.4 VerifySearch

```json
{
  "type": "search.verify",
  "search_id": "uuid",
  "verifier": "agent://validator-1",
  "method": "self-consistency-check",
  "score": 0.92,
  "evidence_chain": ["reason://verification-abc"],
  "signature": "ed25519:..."
}
```

#### 2.5 FinalizeSearch

```json
{
  "type": "search.finalize",
  "search_id": "uuid",
  "answer_node": "reason://agent-42/node-12",
  "path": ["reason://agent-42/node-0", "reason://agent-42/node-3", "reason://agent-42/node-12"],
  "confidence": 0.92,
  "content": "string",
  "signature": "ed25519:..."
}
```

### 3. Capability Advertisement

An agent that supports search execution SHOULD advertise:

```json
{
  "type": "capability://search-execution",
  "parameters": {
    "supported_strategies": ["urn:ss-search:mcts", "urn:ss-search:beam", "urn:ss-search:rag"],
    "max_graph_nodes": 10000,
    "max_depth": 20,
    "supported_evidence_sources": ["knowledge://", "artifact://", "tel://"],
    "budget_constraints": { "max_cost": 1.0, "max_latency_ms": 30000 },
    "verification_methods": ["self-consistency-check", "cross-validator"],
    "supports_safety_contracts": true,
    "supports_human_handover": true
  }
}
```

### 4. Resource Budgeting

Every search MUST declare a budget before execution:

| Field | Description |
|-------|-------------|
| `max_cost` | Maximum compute cost in SS credits |
| `max_latency_ms` | Maximum wall-clock time |
| `max_energy_mj` | Maximum energy budget |
| `max_nodes` | Maximum graph nodes |
| `jurisdiction` | Allowed data residency for search state |

If any budget is exceeded, the execution engine MUST terminate the search and initiate a graceful degradation (RFC-0058).

### 5. Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `budget_exceeded` | Search exceeded resource limits | Freeze graph, notify initiator, option to re-negotiate |
| `safety_contract_violation` | Safety contract precondition not met | Reject search, log via `safeguard://` |
| `node_not_found` | Referenced `reason://` node does not exist | Return error, abort expansion |
| `strategy_not_supported` | Responder does not implement the requested strategy | Return supported strategies as counter-offer |
| `verification_failed` | Search verification score below threshold | Mark search as `unverified`, notify governance |

### 6. Security Considerations

- **Replay Attacks:** All messages MUST include a monotonically increasing sequence number or timestamp, signed by the sender's identity key.
- **Budget Fraud:** The responder MUST verify budget claims against local policy before allocating resources.
- **Verifier Independence:** The verification step SHOULD use a different agent than the one that performed the search to prevent self-deception.

### 7. Conformance

To claim conformance with this RFC, an implementation MUST:

1. Support the search lifecycle states and state transitions defined in §1.
2. Implement the five protocol messages (§2) at minimum as event bus messages.
3. Advertise `capability://search-execution` with supported strategies.
4. Enforce resource budgets (§4) and terminate searches that exceed them.
5. Integrate safety contracts (§2.1) before accepting a search initiation.

### 8. References

- RFC-0070: Search Objects
- RFC-0054: Capability Negotiation
- RFC-0057: Meta-Cognition and Self-Improvement Objects
- RFC-0058: Dynamic Negotiation
