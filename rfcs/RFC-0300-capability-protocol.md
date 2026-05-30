# RFC-0300: Agent Capability Protocol (ACP)

**Status:** Draft  
**Created:** 2026-05-30  
**Layer:** Capability (`ss-capability`)  

## 1. Abstract

This RFC defines the Agent Capability Protocol (ACP), also known as "Semantic DNS" or "Cognitive Routing." ACP shifts network interactions from address-based routing (asking a specific agent for help) to capability-based routing (asking the network for a required skill, and allowing the network to match the best provider).

## 2. Motivation

In a dynamic network of millions of models and agents, hardcoding paths to specific agents is brittle. A highly rated agent might go offline, or a cheaper/faster model might be deployed at the edge. ACP decouples the *intent* (the required skill) from the *executor* (the specific agent).

## 3. Specification

### 3.1 Capability Descriptors

Agents advertise their skills to the network by publishing a `CapabilityDescriptor`. This descriptor is registered in the local `CapabilityRegistry` and propagated through the DHT.

```json
{
  "provider": "agent://legal-expert",
  "capability": "contract_review",
  "accuracy": 0.96,
  "cost": 0.05,
  "latency_ms": 2500,
  "languages": ["en", "cs"],
  "jurisdictions": ["EU"],
  "available": true
}
```

### 3.2 Capability Queries

When an agent needs a subtask executed, it issues a `CapabilityQuery`.

```json
{
  "capability": "contract_review",
  "language": "cs",
  "min_accuracy": 0.90,
  "max_cost": 0.10
}
```

### 3.3 The Matching Algorithm

When a node processes a `CapabilityQuery`, it searches its registry and computes a **Relevance Score** for all matching descriptors.

The default relevance function (which can be overridden by local node policies) is:

```math
Score = (Accuracy \times 0.5) + (LatencyScore \times 0.3) + (CostScore \times 0.2)
```

Where:
- $LatencyScore = 1.0 - \min(\frac{latency\_ms}{30000}, 1.0)$
- $CostScore = 1.0 - \min(\frac{cost}{10.0}, 1.0)$

The node returns the top N matches to the requester.

## 4. Routing Flow

1. **Intent:** Agent A needs a contract reviewed in Czech.
2. **Query:** Agent A broadcasts a `CapabilityQuery` via ACP.
3. **Match:** The network returns Agent B (score: 0.92) and Agent C (score: 0.85).
4. **Execution:** Agent A establishes a direct Sovereign Contract (`contract://`) with Agent B.
5. **Feedback:** After execution, Agent A publishes a Trust Event to the Event Bus, affecting Agent B's future Relevance Score.
