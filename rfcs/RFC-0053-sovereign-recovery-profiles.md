# RFC-0053: Sovereign Recovery Profiles

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0050, RFC-0052

## Abstract

Defines named recovery profiles that encode different continuity requirements for different deployment tiers — from home lab to air-gapped defense deployments.

## Specification

### Profile Definitions

| Profile | AI-RTO | AI-RPO | Fallbacks Required | Playbooks Required | Test Frequency | Audit Level |
|---------|--------|--------|--------------------|--------------------|----------------|-------------|
| Home Lab | 300 s | 60 s | 0 | 0 | None | None |
| Enterprise | 30 s | 1 s | ≥ 1 | ≥ 2 | Monthly | L1 |
| Government | 10 s | 0.5 s | ≥ 2 | ≥ 3 | Weekly | L2 |
| Defense | 5 s | 0.1 s | ≥ 3 | ≥ 5 | Daily | L3 |
| Air-Gapped | 60 s | 5 s | ≥ 2 | ≥ 4 | Weekly | L3 |

### Profile Enforcement

```json
{
  "profile_name": "enterprise",
  "compliance_level": "SECURE_L2",
  "requirements": {
    "min_fallback_models": 1,
    "min_recovery_playbooks": 2,
    "max_ai_rto_seconds": 30,
    "max_ai_rpo_seconds": 1,
    "max_quality_degradation_pct": 15,
    "test_interval_days": 30,
    "provider_diversity_min": 2
  },
  "auto_remediate": true
}
```

### Profile Resolution

1. Node declares its `recovery_profile` in compliance config
2. OASA validator checks all manifest fields against profile requirements
3. Violations generate warnings or blocks based on compliance level
4. `oasa-audit report` includes per-profile pass/fail

### Core Types

```rust
pub struct RecoveryProfile { pub name: String, pub compliance_level: String, pub requirements: ProfileRequirements }
pub struct ProfileRequirements { pub min_fallback_models: u32, pub max_ai_rto_seconds: u64, pub max_ai_rpo_seconds: u64, pub test_interval_days: u64 }
```
