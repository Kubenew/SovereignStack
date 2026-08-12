# Multi-Step Workflow — Governed Orchestration

**Scenario:** A single agent-driven workflow performs several governed actions
against Morpheus in sequence, producing one continuous, verifiable provenance
chain that covers the whole orchestration — not just isolated API calls.

This is the "do it once, do it well, replicate" pattern: the same governance
path (`identity -> capability -> policy -> provenance -> evidence`) is applied
to every step.

---

## Workflow: Deploy a governed ML training cluster

```
agent://ml-platform
  ├── 1. provision-vm   → vm-1001   (governed ALLOW)   ┐
  ├── 2. provision-vm   → vm-1002   (governed ALLOW)   │  one provenance chain
  ├── 3. provision-vm   → vm-1003   (governed ALLOW)   │  chain://morpheus/ml-platform/deploy-0042
  ├── 4. configure-storage → denied (governed DENY)    │  (denial still recorded)
  └── 5. verify-cluster → healthy   (evidence read)    ┘
```

Each step:

1. **Identify** — the agent signs the step request with its Ed25519 key.
2. **Authorize** — the agent holds `capability://compute/provision` and, for
   step 4, is missing `capability://storage/configure` (delegation not granted).
3. **Evaluate** — policy is evaluated per step.
4. **Execute or halt** — ALLOW steps call Morpheus; the DENY step does not.
5. **Evidence** — every step, including the denial, appends to the chain and is
   covered by a single audit-exportable assurance package.

## Why This Matters

A single-API-call demo proves the mechanism. A multi-step workflow proves the
**operational pattern**: autonomous orchestration that is fully auditable end to
end. Regulators, auditors, and CISOs care about the second one.

## Audit Outcome

After the workflow, an auditor can run one command and receive one signed
package covering all five steps:

```
ss-audit export --chain chain://morpheus/ml-platform/deploy-0042
→ assurance-package://morpheus/deploy-0042/2026-08-11
  - 3 governed provisioning actions (ALLOW, signed)
  - 1 governed denial (DENY, signed)
  - 1 health verification (read-only)
  - chain integrity: VERIFIED
  - step signatures: VALID (Ed25519)
```
