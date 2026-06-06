# RFC-0019: Trust & Reputation Scoring

**Status:** Draft | **Type:** Standard | **Created:** 2026-06-03 | **Depends On:** RFC-0001, RFC-0011

## Summary

Defines the trust and reputation scoring system for agents and nodes, enabling capability-based trust decisions.

## Specification

### Trust Score

A composite score (0.0–1.0) combining:

| Factor | Weight | Source |
|--------|--------|--------|
| Identity age | 0.10 | Registry |
| Capability verification rate | 0.25 | Historical |
| Peer endorsements | 0.20 | Federation |
| Provenance completeness | 0.15 | Provenance graph |
| Compliance level | 0.30 | Self-reported |

### Computation

`trust_score = Σ(weight_i × score_i)` where each `score_i` is normalized [0,1].

### Reputation

Reputation is a time-decayed weighted average of trust scores from multiple verifiers. Scores older than `max_age_days` decay exponentially.

### Core Types

`TrustScore`, `ReputationScore`, `Endorsement`, `TrustPolicy`
