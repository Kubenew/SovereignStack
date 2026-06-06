# RFC-0024: Multi-Model Routing

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0030, RFC-0031

## Summary

Defines how inference requests are routed to the optimal model based on capability requirements, performance constraints, cost, and topology locality.

## Specification

### Routing Request

```json
{
  "request_id": "req-001",
  "model_capability": {"task": "reasoning", "min_context": 8192, "quantization": "int4"},
  "constraints": {"max_latency_ms": 500, "max_cost": 0.01, "jurisdiction": "EU"},
  "session_id": "session://abc123"
}
```

### Routing Strategy

1. Filter candidate models by capability requirements
2. Score by composite: `weight_latency × latency_score + weight_cost × cost_score + weight_topology × topology_proximity`
3. Route to highest-scoring node running the model
4. If no local match, fall back to federation (RFC-0008/RFC-0035)

### Core Types

`ModelRouteRequest`, `ModelRouteResult`, `ModelCapability`, `RoutingStrategy`
