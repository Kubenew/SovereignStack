# SovereignStack Morpheus Integration: Golden Path

This document outlines the standard "Golden Path" for demonstrating SovereignStack's governance capabilities over an HPE Morpheus workload.

## Scenario
A request is made to provision a new VM in HPE Morpheus. SovereignStack discovers the workload, evaluates policy, authorizes the action, and records cryptographic provenance. Finally, the generated evidence is independently verified.

## Execution

From the repository root, you can execute the end-to-end demonstration script:

```bash
./demo/morpheus/run.sh
```

### The Workflow Steps

1. **Connect**
   - Connect to the (mock) Morpheus API.
2. **Discover**
   - Discover the target workload and map it to a SovereignStack Identity.
3. **Authorize**
   - Translate the requested operation into SovereignStack Policy and Capability checks.
4. **Execute**
   - (Mock) Perform the VM provisioning in Morpheus.
5. **Record**
   - Record the operation and the Morpheus infrastructure facts into the cryptographic Provenance Chain.
6. **Evidence**
   - Generate an independent, signed `evidence.json` package.
7. **Verify**
   - Independently verify the evidence package without requiring Morpheus API access.

### Expected Output

```text
SovereignStack Morpheus Integration
====================================

Identity             PASS
Capability           PASS
Policy               PASS
Workload Discovery   PASS
Operation            PASS
Provenance           PASS
Evidence             PASS
Tamper Detection     PASS

Core Conformance:    7/7
Security Tests:     10/10
Evidence Integrity: VALID

STATUS: CONFORMANT
```
