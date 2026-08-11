# Governed VM Provisioning — The Killer Demo

**Scenario:** An autonomous AI agent requests VM provisioning against HPE Morpheus.
SovereignStack sits between the agent and Morpheus: it verifies identity, checks
capability, evaluates policy, and records every action as cryptographically
verifiable provenance. Morpheus is never called unless the governing decision is
ALLOW.

This single demo proves the entire SovereignStack core contract —
`identity -> capability -> policy -> provenance -> evidence` — against a real,
recognizable enterprise control plane.

---

## The Architecture in One Picture

```
                    ┌─────────────────────────────────────────┐
                    │              SOVEREIGNSTACK              │
                    │    Trust · Identity · Policy · Evidence  │
                    └─────────────────────────────────────────┘
                                   │
             agent request         │          ALLOW → HTTP
  agent://ml-platform ─────────────┼──────────────────────────►  HPE MORPHEUS
                                   │         (governed call)      POST /api/vms
                                   │
                                   │  DENY  → no API call
                                   │          denial recorded as evidence
```

## Scenario 1 — Authorized Provisioning (ALLOW)

1. The agent `agent://ml-platform` signs a request to provision an 8 vCPU /
   32 GB VM on `prod-vlan-42` using `ubuntu-22.04-lts` in `production`.
2. SovereignStack evaluates:

   | Check | Result |
   |-------|--------|
   | Identity: `agent://ml-platform` → verified signature | PASS |
   | Capability: `capability://compute/provision` granted | PASS |
   | Policy `policy://morpheus/vm-provisioning` | ALLOW |
   | Policy `policy://morpheus/network-access` | ALLOW |
   | Policy `policy://morpheus/resource-limits` | ALLOW |

3. Decision: **ALLOW**. SovereignStack calls Morpheus `POST /api/vms` with the
   governed spec.
4. Morpheus returns the provisioned VM id (`vm-847291`).
5. SovereignStack appends a provenance entry to
   `chain://morpheus/ml-platform/vm-847291` and generates a signed evidence
   package: `evidence://morpheus/provisioning/vm-847291`.
6. Independent verification:

   ```
   ss-audit verify evidence://morpheus/provisioning/vm-847291
   → VERIFIED - chain intact, signatures valid, policy compliant
   ```

## Scenario 2 — Unauthorized Provisioning (DENY)

1. The same agent requests an oversized VM: 64 vCPU / 512 GB on
   `unapproved-network`.
2. SovereignStack evaluates:

   | Check | Result |
   |-------|--------|
   | CPU 64 > max 16 | FAIL |
   | Memory 512 > max 64 | FAIL |
   | Network `unapproved-network` not in approved list | FAIL |

3. Decision: **DENY** with reason `POLICY_VIOLATION`.
4. Morpheus is **not** called.
5. The denial is recorded as a provenance entry and evidence package
   (`evidence://morpheus/denied/provisioning/<ts>`), so even denials are
   auditable and provable.

## Scenario 3 — Tampered Evidence Detection

1. An attacker modifies a recorded evidence record (changes memory from 32 GB
   to 512 GB after the fact).
2. The content hash of the entry no longer matches its recomputed hash; the
   Merkle-style linkage breaks.
3. Verification fails:

   ```
   ss-audit verify evidence://morpheus/provisioning/vm-847291
   → FAILED - chain broken at entry 3
     expected content hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
     actual content hash:   0000000000000000000000000000000000000000000000000000000000000000
     alert: INTEGRITY VIOLATION - evidence may have been modified
   ```

## What This Proves

1. SovereignStack governs real infrastructure, not a toy example.
2. Policy enforcement works in both directions — ALLOW and DENY.
3. Provenance is cryptographically verifiable without access to Morpheus.
4. Tampering is detectable (chain integrity).
5. The flow is end-to-end: agent request -> policy decision -> infrastructure
   action -> signed evidence.

## Positioning Language

- Project documentation: "SovereignStack OASA Profile for HPE Morpheus"
- Integration README: "HPE Morpheus Integration - Conformance Tested"
- Demo: "SovereignStack governing HPE Morpheus: cryptographically verifiable
  autonomous infrastructure"
- Certification badge: "OASA-MORPHEUS-CORE-0.1 Conformant"

Do **not** claim "HPE Certified", "HPE Approved", or "HPE Validated" until an
official HPE relationship exists.

## Running It

See [QUICKSTART.md](../../QUICKSTART.md) for the 15-minute setup, or run the
automated end-to-end tests:

```
python examples/governed-vm-provisioning/demo.py
pytest conformance/tests/ -v
```
