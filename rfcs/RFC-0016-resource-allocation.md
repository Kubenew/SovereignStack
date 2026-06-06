# RFC-0016: Resource Allocation & Accounting

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0003, RFC-0031

## Summary

Defines how compute (GPU/CPU), memory (HBM/DDR), and network bandwidth are allocated, accounted, and enforced across sessions and agents.

## Specification

### Resource Quota

```json
{
  "session_id": "session://abc123",
  "quotas": {
    "vram_gb": {"limit": 16, "used": 12.5, "reserved": 3.5},
    "hbm_gb": {"limit": 80, "used": 64, "reserved": 16},
    "bandwidth_gbps": {"limit": 100, "used": 45, "reserved": 30}
  },
  "priority": "normal",
  "preemptible": false
}
```

### Enforcement

- Hard limits enforced at kernel level
- Preemption priority queue for oversubscription
- Accounting records persisted to audit log (RFC-0022)

### Core Types

`ResourceQuota`, `ResourceUsage`, `AllocationRequest`, `AccountingRecord`
