# QUICKSTART — Governed HPE Morpheus Demo (15 minutes)

This guide runs the full ALLOW/DENY demo against a **mock Morpheus API** that
speaks the same wire protocol as HPE Morpheus. Everything runs on Python 3.10+
with the standard library; Ed25519 signatures use `cryptography` if installed
(highly recommended) with an HMAC fallback.

## Prerequisites

- Python 3.10+ (`python --version`)
- Optional: `pip install cryptography`  (real Ed25519 signatures)
- `pytest` (for the conformance suite)

## 1. Automated End-to-End Demo (fastest)

```bash
cd integrations/hpe-morpheus

# Runs: mock Morpheus -> governed ALLOW -> governed DENY -> tamper detection
python examples/governed-vm-provisioning/demo.py
```

Expected output (abridged):

```
=== SovereignStack x HPE Morpheus - governed VM provisioning demo =====
  Mock Morpheus API: http://127.0.0.1:64025
=== request 1: compliant VM (expect ALLOW) ============================
  Decision: ALLOW
  Reason:   None
  Morpheus: CALLED -> vm-1001
    identity     PASS    signature verified for agent://ml-platform
    capability   PASS    direct grant: capability://compute/provision
    policy       ALLOW   policy://morpheus/network-access: ALLOW; ...
=== request 2: oversized VM on unapproved network (expect DENY) =======
  Decision: DENY
  Reason:   POLICY_VIOLATION
  Morpheus: never called
    policy       DENY    policy://morpheus/network-access: DENY; ...
=== verification: provenance + evidence ===============================
  provenance chain:  VERIFIED
  evidence package:  VERIFIED
  Demo PASSED - governance pipeline verified end to end.
```

## 2. Conformance Suite

```bash
cd integrations/hpe-morpheus
pytest conformance/tests/ -v
```

Covers MOR-001..MOR-010 plus security attacks (replay, signature substitution,
event modification, capability escalation). All tests are self-contained — no
live Morpheus required.

## 3. Manual Walk-Through

Start the mock Morpheus on port 8548:

```bash
cd integrations/hpe-morpheus
python api/morpheus_mock.py --port 8548
```

In a second terminal, drive a governed request using the example request
envelope (which carries the tenant quota needed for an ALLOW):

```bash
cd integrations/hpe-morpheus
python -m api.morpheus_client --endpoint http://localhost:8548 \
  --spec-file examples/governed-vm-provisioning/agent-request.json \
  --quota '{"cpu_remaining": 16, "memory_gb_remaining": 64, "running_vms": 3}'
```

The result is `ALLOW` and Morpheus is called. Repeat with an oversized spec file
to see the `DENY` path — Morpheus is never contacted.

> **Windows PowerShell note:** native argument passing strips inner double
> quotes, so inline `--spec '{"cpu": ...}'` breaks. Use `--spec-file` (a JSON
> file) and `--quota` instead. On bash/Linux both forms work.

## 4. Pointing at a Real Morpheus Instance

When you have access to HPE Morpheus >= 6.0:

```bash
python -m api.morpheus_client --endpoint https://morpheus.example.com \
  --username <service-account> --password <secret> \
  --spec-file <request>.json --quota '{"cpu_remaining": 16, ...}'
```

The client authenticates via `POST /api/auth/token`, maps the authenticated
Morpheus user to the agent identity (the `--agent` binding), and continues
through the same governance pipeline. The mock and the real instance share the
same wire contract (`POST /api/vms`, `/api/auth/token`).

## 5. Verifying Evidence Independently

Evidence packages are self-describing and do not require access to Morpheus:

```python
from evidence.evidence_generator import EvidencePackage
from evidence.evidence_verifier import EvidenceVerifier
from provenance.morpheus_provenance_chain import resolve_key_from

pkg = EvidencePackage.load("evidence-....json")   # or client.last_package
resolver = resolve_key_from({"agent://ml-platform": "<agent public key hex>"})
ok, reasons = EvidenceVerifier().verify(pkg, resolver, "<node public key hex>")
assert ok, reasons   # VERIFIED
```

The audit bundle for MOR-010 aggregates every package into one report:

```bash
python -m pytest conformance/tests/test_audit_export.py -v --report-dir=reports
```
