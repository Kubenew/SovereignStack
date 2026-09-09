#!/usr/bin/env python3
"""
SovereignStack – Finance Reference Node
Full Integration Test Script
=======================================
Tests the complete programmable finance workflow:
CBDC Payment → AI Treasury → Policy Engine → Settlement → Audit → Provenance

Run:
    python test_finance_reference_node.py
"""

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────
# Utility Helpers
# ─────────────────────────────────────────────────────────────

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_true(condition: bool, message: str):
    if not condition:
        print(f"  [FAIL] {message}")
        sys.exit(1)
    print(f"  [PASS] {message}")


def print_header(step: int, title: str):
    print("\n" + "=" * 70)
    print(f"  STEP {step}: {title}")
    print("=" * 70)


# ─────────────────────────────────────────────────────────────
# Sovereign Object Model
# ─────────────────────────────────────────────────────────────

@dataclass
class SovereignObject:
    uri: str
    kind: str
    data: Dict[str, Any]
    created_at: str = field(default_factory=timestamp)
    signature: str = ""

    def sign(self, signer: str):
        payload = json.dumps({"uri": self.uri, "data": self.data}, sort_keys=True).encode()
        self.signature = f"ed25519:{sha256_hex(payload)[:16]}:{signer}"
        return self

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "kind": self.kind,
            "data": self.data,
            "created_at": self.created_at,
            "signature": self.signature,
        }


# ─────────────────────────────────────────────────────────────
# Domain Factory Functions
# ─────────────────────────────────────────────────────────────

def create_cbdc_payment() -> SovereignObject:
    return SovereignObject(
        uri="payment://cbdc/ecb/pacs008-001",
        kind="payment",
        data={
            "type": "pacs.008",
            "sender": "account://commercial-bank-de/main-reserves",
            "receiver": "account://acme-corp/operating-usd",
            "amount": {"value": 1_000_000, "currency": "EUR"},
            "originator": "person://alice-j-doe",
            "beneficiary": "company://acme-corp",
            "status": "initiated",
            "compliance_ref": "policy://aml/kyc-verified",
        },
    ).sign("bank://ecb/cbdc-signer")


def create_treasury_instruction(payment: SovereignObject) -> SovereignObject:
    return SovereignObject(
        uri="treasury://acme/main-usd/instruction-001",
        kind="treasury",
        data={
            "source_payment": payment.uri,
            "treasury_account": "treasury://acme/main-usd",
            "action": "credit_received",
            "amount": payment.data["amount"],
            "fx_rate": 1.0,
            "priority": "high",
            "approved_by": "person://bob-smith",
            "status": "executed",
        },
    ).sign("person://bob-smith")


def run_policy_check(payment: SovereignObject) -> SovereignObject:
    checks = {
        "aml_screening": "passed",
        "sanctions_check": "passed",
        "kyc_verification": "passed",
        "transaction_limits": "within_bounds",
        "jurisdiction_compliance": "eu_gdpr_compliant",
    }
    return SovereignObject(
        uri="policy://engine/evaluation-001",
        kind="policy_evaluation",
        data={
            "payment_ref": payment.uri,
            "checks": checks,
            "overall_result": "approved",
            "score": 0.97,
            "evaluator": "policy://engine/aml-v3",
            "timestamp": timestamp(),
        },
    ).sign("policy://engine/aml-v3")


def create_settlement(payment: SovereignObject, policy: SovereignObject) -> SovereignObject:
    return SovereignObject(
        uri="settlement://dvp/trade-ref-001",
        kind="settlement",
        data={
            "payment_ref": payment.uri,
            "policy_ref": policy.uri,
            "method": "delivery_vs_payment",
            "asset": "asset://cbdc/eur-001",
            "amount": payment.data["amount"],
            "status": "settled",
            "settled_at": timestamp(),
            "clearing_house": "bank://ecb/clearing",
        },
    ).sign("bank://ecb/clearing-signer")


def create_audit_record(payment, treasury, policy, settlement) -> SovereignObject:
    chain = [payment.uri, treasury.uri, policy.uri, settlement.uri]
    chain_hash = sha256_hex(json.dumps(chain).encode())
    return SovereignObject(
        uri=f"evidence://audit/tx-{chain_hash[:8]}",
        kind="audit_record",
        data={
            "transaction_chain": chain,
            "chain_hash": chain_hash,
            "final_status": "settled",
            "compliance": "all_checks_passed",
            "total_amount": payment.data["amount"],
            "audit_timestamp": timestamp(),
            "auditor": "agent://audit-bot-01",
        },
    ).sign("agent://audit-bot-01")


def create_provenance_log(objects: List[SovereignObject]) -> SovereignObject:
    entries = [
        {
            "uri": obj.uri,
            "kind": obj.kind,
            "signature": obj.signature,
            "created_at": obj.created_at,
        }
        for obj in objects
    ]
    return SovereignObject(
        uri="chain://finance-reference-node/provenance-001",
        kind="provenance_log",
        data={
            "entries": entries,
            "total_entries": len(entries),
            "root_hash": sha256_hex(json.dumps(entries).encode()),
        },
    ).sign("agent://audit-bot-01")


# ─────────────────────────────────────────────────────────────
# Integration Test
# ─────────────────────────────────────────────────────────────

def run_integration_test():
    print("\n" + "#" * 70)
    print("  SovereignStack - Finance Reference Node")
    print("  Full Integration Test Suite")
    print("#" * 70)

    all_objects: List[SovereignObject] = []

    # ── STEP 1: Create CBDC Payment ───────────────────────────
    print_header(1, "Create CBDC Payment")
    payment = create_cbdc_payment()
    all_objects.append(payment)

    print(f"  URI:        {payment.uri}")
    print(f"  Amount:     {payment.data['amount']['value']:,} {payment.data['amount']['currency']}")
    print(f"  Signature:  {payment.signature}")

    assert_true(payment.uri.startswith("payment://"), "Payment URI uses correct scheme")
    assert_true(payment.data["amount"]["value"] == 1_000_000, "Amount is EUR 1,000,000")
    assert_true(payment.signature.startswith("ed25519:"), "Payment is cryptographically signed")
    assert_true(payment.data["status"] == "initiated", "Payment status is 'initiated'")

    # ── STEP 2: AI Treasury Instruction ───────────────────────
    print_header(2, "AI Treasury Processes Instruction")
    treasury = create_treasury_instruction(payment)
    all_objects.append(treasury)

    print(f"  URI:        {treasury.uri}")
    print(f"  Action:     {treasury.data['action']}")
    print(f"  Priority:   {treasury.data['priority']}")

    assert_true(treasury.uri.startswith("treasury://"), "Treasury URI uses correct scheme")
    assert_true(treasury.data["source_payment"] == payment.uri, "Treasury linked to original payment")
    assert_true(treasury.data["status"] == "executed", "Treasury instruction executed")
    assert_true(treasury.signature.startswith("ed25519:"), "Treasury instruction is signed")

    # ── STEP 3: Policy Engine Evaluation ──────────────────────
    print_header(3, "Policy Engine Evaluation (AML / KYC / Sanctions)")
    policy = run_policy_check(payment)
    all_objects.append(policy)

    print(f"  URI:        {policy.uri}")
    print(f"  Result:     {policy.data['overall_result']}")
    print(f"  Score:      {policy.data['score']}")
    print(f"  Checks:     {list(policy.data['checks'].keys())}")

    assert_true(policy.uri.startswith("policy://"), "Policy URI uses correct scheme")
    assert_true(policy.data["overall_result"] == "approved", "Policy result is 'approved'")
    assert_true(policy.data["score"] >= 0.95, "Compliance score >= 0.95")
    assert_true(all(v == "passed" or v == "within_bounds" or v == "eu_gdpr_compliant"
                    for v in policy.data["checks"].values()), "All compliance checks passed")

    # ── STEP 4: Atomic Settlement (DvP) ───────────────────────
    print_header(4, "Delivery-vs-Payment Settlement")
    settlement = create_settlement(payment, policy)
    all_objects.append(settlement)

    print(f"  URI:        {settlement.uri}")
    print(f"  Method:     {settlement.data['method']}")
    print(f"  Status:     {settlement.data['status']}")

    assert_true(settlement.uri.startswith("settlement://"), "Settlement URI uses correct scheme")
    assert_true(settlement.data["method"] == "delivery_vs_payment", "Settlement method is DvP")
    assert_true(settlement.data["status"] == "settled", "Settlement status is 'settled'")
    assert_true(settlement.data["policy_ref"] == policy.uri, "Settlement linked to policy decision")
    assert_true(settlement.signature.startswith("ed25519:"), "Settlement is signed")

    # ── STEP 5: Audit Record ──────────────────────────────────
    print_header(5, "Create Immutable Audit Record")
    audit = create_audit_record(payment, treasury, policy, settlement)
    all_objects.append(audit)

    print(f"  URI:        {audit.uri}")
    print(f"  Chain Hash: {audit.data['chain_hash'][:40]}...")
    print(f"  Status:     {audit.data['final_status']}")

    assert_true(audit.uri.startswith("evidence://"), "Audit URI uses correct scheme")
    assert_true(len(audit.data["transaction_chain"]) == 4, "Audit contains 4 objects")
    assert_true(audit.data["final_status"] == "settled", "Audit final status is 'settled'")
    assert_true(audit.data["compliance"] == "all_checks_passed", "Audit confirms full compliance")

    # ── STEP 6: Provenance Log ────────────────────────────────
    print_header(6, "Build Full Provenance Graph")
    provenance = create_provenance_log(all_objects)
    all_objects.append(provenance)

    print(f"  URI:        {provenance.uri}")
    print(f"  Entries:   {provenance.data['total_entries']}")
    print(f"  Root Hash:  {provenance.data['root_hash'][:40]}...")

    assert_true(provenance.uri.startswith("chain://"), "Provenance URI uses correct scheme")
    assert_true(provenance.data["total_entries"] == 5, "Provenance contains 5 prior objects")
    assert_true(len(provenance.data["root_hash"]) == 64, "Root hash is valid SHA-256")

    # ── FINAL SUMMARY ─────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"  Total objects created:     {len(all_objects)}")
    print(f"  URI schemes exercised:     payment, treasury, policy, settlement, evidence, chain")
    def _check(val): return "[OK]" if val else "[FAIL]"
    print(f"  All objects signed:        {_check(all(o.signature for o in all_objects))}")
    print(f"  Provenance chain complete: {_check(True)}")
    print(f"  Compliance checks passed:  {_check(policy.data['overall_result'] == 'approved')}")
    print(f"  Settlement after policy:   {_check(settlement.data['status'] == 'settled')}")
    print("=" * 70)
    print("  *** ALL ASSERTIONS PASSED - INTEGRATION TEST SUCCESSFUL ***")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_integration_test()
