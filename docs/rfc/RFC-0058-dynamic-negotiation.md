# OASA RFC-0058: Heterogeneous Multi-Agent Task Negotiation & Degradation Contracts

**Status:** Proposed
**Author:** SovereignStack Core Architecture Group
**Date:** July 2026

---

## 1. Objective
This specification formalizes the protocol mechanics for dynamic runtime capability trade-offs when multi-model agent clusters scale across asymmetric hardware networks. It guarantees graceful degradation of cognitive complexity rather than complete execution failure under high link saturation.

## 2. Protocol Invariants

### 2.1 Symmetric Capability Handshakes
Connecting execution nodes MUST broadcast their current feature capabilities via signed `protocol://` arrays. Peers will negotiate down to the highest mutually available protocol revision to eliminate serialization mismatches across old or minimal edge kernels.

### 2.2 Graceful Cognitive Degradation (Load Shedding)
When local telemetry signals indicate link starvation (e.g., node bandwidth dropping below 30% or prompt queue depth exceeding 200 items), swarms MUST invoke the following priority cascade:
1. **Full Reasoning Mesh Mode (`reason://`):** Dense Monte Carlo Tree Search across distributed parameters.
2. **Fallback Lean Optimization Mode (`model://`):** Shifting from high-compute deep reasoning layers to fast, low-parameter models.
3. **Fail-Secure Serialization Mode:** Freezing speculative paths, pushing live token states to local key-value caches (`kv://`), and routing urgent control planes back to human interfaces (`human://`).

## 3. Threat Vector Mitigation
* **Malicious Capability Downgrading:** To prevent bad actors from intentionally downgrading protocol versions to exploit known vulnerabilities, all capability handshakes MUST be signed with the node's identity key (`identity://`). Peers MUST reject unsigned or mismatched capability advertisements.
* **Resource Exhaustion via Lease Spam:** The Circuit Breaker (RFC-0055) MUST rate-limit lease requests per agent identity. Excessive lease creation triggers automatic blacklisting via `safeguard://`.

## 4. Integration Points

| RFC | Component | Role |
|-----|-----------|------|
| RFC-0049 | World Model & Planning | Supplies environmental context for degradation decisions |
| RFC-0050 | Cognitive Leases | Manages resource TTL under constrained conditions |
| RFC-0054 | Capability Negotiation | Offer/accept/reject cycle used during handshake |
| RFC-0055 | Circuit Breaker | Enforces rate limits and triggers fail-secure mode |
| RFC-0056 | Zero-Knowledge Alignment | Verifies degradation decisions remain values-aligned |

## 5. Degradation Contract Schema

```json
{
  "contract_version": "1.0",
  "node_id": "node://eu-frankfurt-01",
  "timestamp_ns": 1789200000000000000,
  "original_capabilities": ["reason://full-mcts", "model://gpt-4", "kv://distributed"],
  "negotiated_capabilities": ["model://llama-3b", "kv://local-only"],
  "reason": "bandwidth_dropped_below_30pct",
  "proof_uri": "evidence://degradation-contract/abc123"
}
```
