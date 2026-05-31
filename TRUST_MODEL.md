# SovereignStack Trust Model

**Version:** 1.0
**Status:** Draft

## Core Philosophy

**Capability-Based Security** (Principle 6) + **Verifiable Everything** (Principle 5) = Zero Implicit Trust.

## Trust Layers

1. **Cryptographic Trust** — Signatures and keys
2. **Capability Trust** — Explicit permissions only
3. **Provenance Trust** — Full audit trail
4. **Reputation Trust** — Optional, revocable scoring
5. **Jurisdictional Trust** — Policy-enforced data residency

## Key Mechanisms

- All actions require a valid capability
- Capabilities are revocable and time-bound
- Human Override always possible (Principle 7)
- Trust is **local-first**, federation is opt-in

## Threat Model

- Malicious nodes
- Compromised agents
- Network partitioning
- Supply chain attacks

Mitigations are defined in SECURITY.md.
