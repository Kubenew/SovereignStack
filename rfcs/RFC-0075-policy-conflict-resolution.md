# RFC-0075: Policy Composition, Jurisdiction & Conflict Resolution

**Status:** Active | **Type:** Standard | **Created:** 2026-08-07 | **Depends On:** RFC-0020, RFC-0021, RFC-0047, RFC-0060  
**Related:** [SIRA](../SIRA.md), [TRUST_MODEL](../TRUST_MODEL.md)

## Abstract

Defines the normative framework for **composing policy from multiple authorities** and **resolving policy conflicts** that arise when a single autonomous action is simultaneously governed by overlapping policies — e.g., organizational policy, jurisdictional law, industry regulation, and delegated third-party policy.

This RFC is the enforcement-layer companion to RFC-0060 (the Cognitive Mesh Architecture). It introduces:

- A **policy composition model** in which every applicable policy contributes constraints to an action
- A **conflict taxonomy** (Types A–E) that classifies the way policies disagree
- A **resolution hierarchy** that deterministically selects the governing rule
- A **safe-halt default** — when conflict cannot be resolved, the action MUST NOT proceed and MUST be escalated to a human
- A **Conflict Evidence Object** (`conflict://`) that makes every resolution (or escalation) cryptographically auditable

## Motivation

Autonomous agents increasingly act across boundaries that were designed for human-managed rulebooks:

- A treasury agent executes a cross-border CBDC settlement.
- A compliance agent routes a payment that is legal in the sender jurisdiction but prohibited in the recipient jurisdiction.
- A trading agent follows an internal policy that contradicts a newly signed MiCA requirement.

Today, such conflicts are handled implicitly — by whichever policy engine evaluates last, by whichever rule an engineer hard-coded first, or worse, by the model guessing. None of these are acceptable for regulated, auditable autonomy.

RFC-0075 makes conflict an **explicit, first-class, and auditable event** rather than an emergent bug.

## Specification

### 1. Policy Composition Model

Every action `A` is governed by a set of applicable policies:

```
P(A) = { p₁, p₂, ..., pₙ }
```

A policy is applicable if its **scope predicate** matches the action's context (actor, subject, jurisdiction, capability, resource, time window). Each policy contributes zero or more constraints. An action is authorized if and only if **all** applicable policies permit it:

```
authorized(A) ⇔ ∀ p ∈ P(A): permit(A, p)
```

There is no notion of "majority" or "priority-weighted averaging" at this stage — every applicable policy has a veto. Priority enters only at the **resolution** stage (Section 4), and only when two policies impose **contradictory** requirements on the same action.

### 2. Policy Sources & Jurisdiction

Policies are sourced from a **policy graph** (extending RFC-0020):

| Source | Example | Authority |
|--------|---------|-----------|
| Organizational | `policy://org/acceptable-use` | Principal owner |
| Jurisdictional | `policy://jur/mi-ca/art-23` | Law of a territory |
| Industrial | `policy://industry/pci-dss/3.2` | Sector body |
| Delegated | `policy://principal/portfolio-limits` | Third party via capability delegation (RFC-0026) |
| Constitutional | `policy://system/oasa-constitution` | Platform-level invariants |

Each policy MUST declare:

- **jurisdiction** — the legal territory whose law it encodes or serves
- **effective range** — subjects, capabilities, and resources it governs
- **supremacy class** — see Section 4
- **precedence key** — optional explicit priority declared by a mutually trusted authority

### 3. Conflict Taxonomy

A conflict exists when two applicable policies impose requirements on the same action that cannot be simultaneously satisfied. Conflicts are classified:

| Type | Name | Definition | Example |
|------|------|------------|---------|
| **A** | Effect Contradiction | Two policies require mutually exclusive outcomes | "Execute transfer" vs "Hold all transfers for review" |
| **B** | Obligation Collision | Two policies impose incompatible duties on the actor | "Report within 24h" vs "Withhold pending investigation" |
| **C** | Scope Ambiguity | Overlapping scopes are not strictly ordered; both claim governance | Territorial vs organizational data-residency rules |
| **D** | Capability Inconsistency | Policies disagree on whether the actor *may* hold a capability | Delegation permits; org policy forbids |
| **E** | Temporal Conflict | Rules that are individually valid but contradictory at a point in time | Sunset clause vs evergreen prohibition |

Type is determined structurally — not by the model — so that auditors can reproduce the classification from the policy texts alone.

### 4. Resolution Hierarchy

When a conflict is detected, resolution proceeds down a **deterministic hierarchy**. The first rule that produces an unambiguous outcome governs:

1. **Hard Supremacy** — a policy may declare a **hard-supremacy invariant** (e.g., constitutional/legal minimums: "no rule may authorize violating OASA Axiom 1 — Zero Exfiltration"). Hard-supremacy policies always win.
2. **Explicit Precedence** — a mutually trusted authority has declared `precedes` relationships between the conflicting policies.
3. **Specificity** — the policy whose scope is more specific to the action governs (`policy://jur/eu-ai-act/art-14` beats `policy://jur/eu-ai-act`).
4. **Temporal** — the later-enacted policy governs, unless a sunset clause states otherwise.
5. **Delegation Chain** — for delegated policies, resolution follows the delegation chain upward (RFC-0026), preferring the policy of the party closest to the principal.
6. **Escalation (default)** — if no rule resolves the conflict, the action **MUST NOT proceed**. The conflict is escalated to a human override (RFC-0047) and recorded as a Conflict Evidence Object.

### 5. Safe-Halt Default

The default outcome of any **unresolved** conflict is **safe halt**:

- The action is not executed.
- Any partially initiated side effects are rolled back to the last verified checkpoint.
- A human escalation ticket is created.
- The full conflict context is frozen and signed.

The agent must never "pick a best guess." A halt that a human later resolves is an audit event; a guess is a liability.

### 6. Conflict Evidence Object

Every conflict, resolution, and escalation MUST produce an evidence object addressed at `conflict://`:

```
conflict://<node>/<sha256-txn>
```

| Field | Description |
|-------|-------------|
| `action` | The action under dispute |
| `policies` | The set `P(A)` with full text hashes |
| `type` | Conflict taxonomy class (A–E) |
| `resolution` | The hierarchy rule applied (or `escalated`) |
| `decision` | `permit` / `deny` / `escalated` |
| `human_override` | Reference to RFC-0047 override, if any |
| `parent` | Chain of upstream evidence objects |
| `signature` | Node signature binding the above |

Evidence objects are appended to the same Merkle-ordered store as all other provenance (RFC-0013, RFC-0018), so the full resolution trace is tamper-evident.

### 7. Conflict Resolution Service (CRS)

The runtime component implementing this RFC is the **Conflict Resolution Service**:

- Evaluates `P(A)` per action
- Detects and classifies conflicts
- Attempts resolution per the hierarchy
- Enforces the safe-halt default
- Emits `conflict://` evidence objects
- Maintains a human-escalation queue with signed, timestamped tickets

The CRS is mandatory for **OASA Level 3** autonomous execution and above.

## Conformance

A node conforms to RFC-0075 when:

1. It evaluates the full applicable policy set for every governed action.
2. It detects and classifies conflicts using the Type A–E taxonomy.
3. It applies the resolution hierarchy in the prescribed order.
4. It halts and escalates on unresolved conflict (no guessing).
5. It emits tamper-evident `conflict://` evidence for every conflict event.
6. It maps human overrides to RFC-0047 and records them as evidence.

## References

- RFC-0020 — Policy Enforcement
- RFC-0021 — Jurisdiction & Data Residency
- RFC-0026 — Capability Delegation
- RFC-0047 — Human Override Protocol
- RFC-0060 — Cognitive Mesh Architecture
- RFC-0076 — OASA Continuous Assurance Engine (consumes conflict evidence)
