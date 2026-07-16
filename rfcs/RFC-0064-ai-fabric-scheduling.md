# RFC-0064: AI Fabric Scheduling Protocol (AFS)

**Status:** Draft | **Type:** Standard | **Created:** 2026-07-16 | **Depends On:** RFC-0030, RFC-0031, RFC-0060  
**Protocol ID:** AFS

## Abstract

Extends existing fabric RFCs with cognitive-aware scheduling. AFS defines how inference requests and agent sessions are scheduled across an AI fabric by optimizing for multi-dimensional constraints: GPU topology, KV-cache locality, trust domains, jurisdiction, energy, latency, and cognitive economics.

## Motivation

Traditional Kubernetes scheduling optimizes for CPU and RAM availability. AI workloads require scheduling based on data gravity (KV caches), hardware topology (NVLink/Infiniband), and cognitive constraints (trust, jurisdiction). AFS provides a standardized protocol for scheduling autonomous workloads.

## Specification

### 1. Multi-Dimensional Optimization

The AFS scheduler (`scheduler://`) optimizes placement across the following dimensions:

1. **Topology/Locality**: Place execution near existing KV caches (`kv://`) or required data (`knowledge://`).
2. **Hardware Affinity**: Match model requirements (e.g., INT4 quantization, FlashAttention) to hardware capabilities.
3. **Trust & Jurisdiction**: Ensure execution only happens on nodes meeting policy constraints (e.g., `policy://eu-data-residency`).
4. **Economics**: Optimize for cost constraints using Cognitive Economics resource contracts.

### 2. Cognitive Economics Resource Contracts

Allocation is governed by explicit resource contracts:

```json
{
  "uri": "compute://zcube-a/alloc-001",
  "type": "compute",
  "quadrant": "federation",
  "owner": "session://finance-q3",
  "resources": {
    "gpu_hours": 10,
    "vram_gb": 80
  },
  "constraints": {
    "max_cost": 5.00,
    "currency": "USD"
  }
}
```

Other resource types include `memory://`, `bandwidth://`, `storage://`, and `energy://`.

### 3. Scheduling Request

```json
{
  "action": "schedule",
  "workload": "agent://reasoning/math",
  "session": "session://finance-q3",
  "requirements": {
    "min_vram_gb": 40,
    "capabilities": ["flash_attention_2"]
  },
  "locality_preference": "kv://sha256:7a92ff01...",
  "resource_contract": "compute://zcube-a/alloc-001"
}
```

### 4. Scheduling Response

```json
{
  "status": "scheduled",
  "node": "node://zcube-a/gpu-003",
  "estimated_start": "2026-07-16T12:05:00Z",
  "allocated_resources": ["compute://zcube-a/alloc-001"]
}
```

### 5. Preemption and Suspend

The scheduler MAY preempt active sessions if higher-priority workloads arrive. Preemption triggers a `checkpoint://` creation via SXP (RFC-0062), allowing the session to be resumed later or migrated.

## Core Types

```rust
pub struct SchedulingRequest {
    pub workload: SovereignUri,
    pub session: SovereignUri,
    pub requirements: HardwareRequirements,
    pub locality_preference: Option<SovereignUri>,
    pub resource_contract: Option<SovereignUri>,
}

pub struct HardwareRequirements {
    pub min_vram_gb: u32,
    pub capabilities: Vec<String>,
}

pub struct ResourceContract {
    pub uri: SovereignUri,
    pub resource_type: ResourceType,
    pub quantity: f64,
    pub constraints: CostConstraints,
}

pub enum ResourceType {
    Compute,
    Memory,
    Bandwidth,
    Storage,
    Energy,
}
```

## Security Considerations

- **Jurisdiction Enforcement**: The scheduler MUST verify that the selected node complies with the jurisdiction policies of the session and its data.
- **Resource Exhaustion**: The scheduler MUST enforce resource quotas to prevent denial-of-service via unbounded compute requests.

## Conformance Impact

- Required for **SIRA-3** conformance
- Integrates with RFC-0031 (KV Locality Scheduling)
