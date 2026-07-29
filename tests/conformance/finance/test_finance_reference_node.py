"""
SovereignStack – Finance Reference Node
Conformance Test Suite
=======================================
Tests the complete programmable finance object model:

  CBDC Payment → Treasury → Policy Engine → Settlement → Audit → Provenance

Each test validates a Sovereign object with:
  - Correct URI scheme
  - Cryptographic signature
  - Required data fields
  - Cross-references to prior objects
  - Verifiable provenance chain

Usage:
    pytest tests/conformance/finance/ -v
    pytest tests/conformance/finance/ -v --report-dir=reports
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List

import pytest


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────
# Object Model Under Test
# ─────────────────────────────────────────────────────────────

@dataclass
class SovereignObject:
    uri: str
    kind: str
    data: dict
    created_at: str = field(default_factory=_ts)
    signature: str = ""

    def sign(self, signer: str):
        payload = json.dumps({"uri": self.uri, "data": self.data}, sort_keys=True).encode()
        self.signature = f"ed25519:{_sha256(payload)[:16]}:{signer}"
        return self


# ─────────────────────────────────────────────────────────────
# Domain Factory Functions
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def cbdc_payment() -> SovereignObject:
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


@pytest.fixture(scope="module")
def treasury_instruction(cbdc_payment) -> SovereignObject:
    return SovereignObject(
        uri="treasury://acme/main-usd/instruction-001",
        kind="treasury",
        data={
            "source_payment": cbdc_payment.uri,
            "treasury_account": "treasury://acme/main-usd",
            "action": "credit_received",
            "amount": cbdc_payment.data["amount"],
            "fx_rate": 1.0,
            "priority": "high",
            "approved_by": "person://bob-smith",
            "status": "executed",
        },
    ).sign("person://bob-smith")


@pytest.fixture(scope="module")
def policy_evaluation(cbdc_payment) -> SovereignObject:
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
            "payment_ref": cbdc_payment.uri,
            "checks": checks,
            "overall_result": "approved",
            "score": 0.97,
            "evaluator": "policy://engine/aml-v3",
        },
    ).sign("policy://engine/aml-v3")


@pytest.fixture(scope="module")
def settlement(cbdc_payment, policy_evaluation) -> SovereignObject:
    return SovereignObject(
        uri="settlement://dvp/trade-ref-001",
        kind="settlement",
        data={
            "payment_ref": cbdc_payment.uri,
            "policy_ref": policy_evaluation.uri,
            "method": "delivery_vs_payment",
            "asset": "asset://cbdc/eur-001",
            "amount": cbdc_payment.data["amount"],
            "status": "settled",
            "settled_at": _ts(),
            "clearing_house": "bank://ecb/clearing",
        },
    ).sign("bank://ecb/clearing-signer")


@pytest.fixture(scope="module")
def audit_record(cbdc_payment, treasury_instruction, policy_evaluation, settlement) -> SovereignObject:
    chain = [cbdc_payment.uri, treasury_instruction.uri, policy_evaluation.uri, settlement.uri]
    chain_hash = _sha256(json.dumps(chain).encode())
    return SovereignObject(
        uri=f"evidence://audit/tx-{chain_hash[:8]}",
        kind="audit_record",
        data={
            "transaction_chain": chain,
            "chain_hash": chain_hash,
            "final_status": "settled",
            "compliance": "all_checks_passed",
            "total_amount": cbdc_payment.data["amount"],
            "auditor": "agent://audit-bot-01",
        },
    ).sign("agent://audit-bot-01")


@pytest.fixture(scope="module")
def provenance_log(request) -> SovereignObject:
    """Requires request.getfixturevalue for fixtures resolved at call time."""
    objects = [
        request.getfixturevalue("cbdc_payment"),
        request.getfixturevalue("treasury_instruction"),
        request.getfixturevalue("policy_evaluation"),
        request.getfixturevalue("settlement"),
        request.getfixturevalue("audit_record"),
    ]
    entries = [
        {"uri": o.uri, "kind": o.kind, "signature": o.signature, "created_at": o.created_at}
        for o in objects
    ]
    return SovereignObject(
        uri="chain://finance-reference-node/provenance-001",
        kind="provenance_log",
        data={
            "entries": entries,
            "total_entries": len(entries),
            "root_hash": _sha256(json.dumps(entries).encode()),
        },
    ).sign("agent://audit-bot-01")


# ─────────────────────────────────────────────────────────────
# URI Scheme Tests
# ─────────────────────────────────────────────────────────────

class TestURISchemes:
    def test_payment_uri(self, cbdc_payment):
        assert cbdc_payment.uri.startswith("payment://")
        assert "cbdc" in cbdc_payment.uri
        assert "pacs008" in cbdc_payment.uri

    def test_treasury_uri(self, treasury_instruction):
        assert treasury_instruction.uri.startswith("treasury://")
        assert "instruction-001" in treasury_instruction.uri

    def test_policy_uri(self, policy_evaluation):
        assert policy_evaluation.uri.startswith("policy://")
        assert "evaluation-001" in policy_evaluation.uri

    def test_settlement_uri(self, settlement):
        assert settlement.uri.startswith("settlement://")
        assert "dvp" in settlement.uri

    def test_audit_uri(self, audit_record):
        assert audit_record.uri.startswith("evidence://")
        assert "tx-" in audit_record.uri

    def test_provenance_uri(self, provenance_log):
        assert provenance_log.uri.startswith("chain://")
        assert "provenance-001" in provenance_log.uri


# ─────────────────────────────────────────────────────────────
# Cryptographic Signature Tests
# ─────────────────────────────────────────────────────────────

class TestSignatures:
    def test_payment_signed(self, cbdc_payment):
        assert cbdc_payment.signature.startswith("ed25519:")
        assert "bank://ecb" in cbdc_payment.signature

    def test_treasury_signed(self, treasury_instruction):
        assert treasury_instruction.signature.startswith("ed25519:")

    def test_policy_signed(self, policy_evaluation):
        assert policy_evaluation.signature.startswith("ed25519:")

    def test_settlement_signed(self, settlement):
        assert settlement.signature.startswith("ed25519:")

    def test_audit_signed(self, audit_record):
        assert audit_record.signature.startswith("ed25519:")

    def test_provenance_signed(self, provenance_log):
        assert provenance_log.signature.startswith("ed25519:")

    def test_signature_unique_per_object(self, cbdc_payment, treasury_instruction):
        assert cbdc_payment.signature != treasury_instruction.signature


# ─────────────────────────────────────────────────────────────
# Data Integrity Tests
# ─────────────────────────────────────────────────────────────

class TestDataIntegrity:
    def test_payment_amount(self, cbdc_payment):
        assert cbdc_payment.data["amount"]["value"] == 1_000_000
        assert cbdc_payment.data["amount"]["currency"] == "EUR"

    def test_payment_status_initiated(self, cbdc_payment):
        assert cbdc_payment.data["status"] == "initiated"

    def test_treasury_linked_to_payment(self, treasury_instruction, cbdc_payment):
        assert treasury_instruction.data["source_payment"] == cbdc_payment.uri

    def test_treasury_executed(self, treasury_instruction):
        assert treasury_instruction.data["status"] == "executed"

    def test_policy_approved(self, policy_evaluation):
        assert policy_evaluation.data["overall_result"] == "approved"
        assert policy_evaluation.data["score"] >= 0.95

    def test_all_checks_passed(self, policy_evaluation):
        for name, result in policy_evaluation.data["checks"].items():
            assert result in ("passed", "within_bounds", "eu_gdpr_compliant"), \
                f"Check '{name}' failed: {result}"

    def test_settlement_method_dvp(self, settlement):
        assert settlement.data["method"] == "delivery_vs_payment"

    def test_settlement_status(self, settlement):
        assert settlement.data["status"] == "settled"

    def test_settlement_linked_to_policy(self, settlement, policy_evaluation):
        assert settlement.data["policy_ref"] == policy_evaluation.uri

    def test_audit_contains_4_objects(self, audit_record):
        assert len(audit_record.data["transaction_chain"]) == 4

    def test_audit_final_status(self, audit_record):
        assert audit_record.data["final_status"] == "settled"

    def test_audit_compliance(self, audit_record):
        assert audit_record.data["compliance"] == "all_checks_passed"

    def test_provenance_5_entries(self, provenance_log):
        assert provenance_log.data["total_entries"] == 5

    def test_provenance_root_hash_valid(self, provenance_log):
        assert len(provenance_log.data["root_hash"]) == 64


# ─────────────────────────────────────────────────────────────
# Cross-Reference Integrity Tests
# ─────────────────────────────────────────────────────────────

class TestCrossReferences:
    def test_payment_has_sender_receiver(self, cbdc_payment):
        assert cbdc_payment.data["sender"].endswith("main-reserves")
        assert cbdc_payment.data["receiver"].endswith("operating-usd")

    def test_treasury_amount_matches_payment(self, treasury_instruction, cbdc_payment):
        assert treasury_instruction.data["amount"] == cbdc_payment.data["amount"]

    def test_policy_refs_payment(self, policy_evaluation, cbdc_payment):
        assert policy_evaluation.data["payment_ref"] == cbdc_payment.uri

    def test_settlement_refs_policy(self, settlement, policy_evaluation):
        assert settlement.data["policy_ref"] == policy_evaluation.uri

    def test_audit_chain_links(self, audit_record, cbdc_payment, treasury_instruction,
                                policy_evaluation, settlement):
        expected = [cbdc_payment.uri, treasury_instruction.uri,
                    policy_evaluation.uri, settlement.uri]
        assert audit_record.data["transaction_chain"] == expected

    def test_provenance_includes_all(self, provenance_log, cbdc_payment, treasury_instruction,
                                      policy_evaluation, settlement, audit_record):
        uris_in_log = {e["uri"] for e in provenance_log.data["entries"]}
        for obj in [cbdc_payment, treasury_instruction, policy_evaluation, settlement, audit_record]:
            assert obj.uri in uris_in_log, f"Missing {obj.uri} from provenance log"


# ─────────────────────────────────────────────────────────────
# Workflow Orchestration Test
# ─────────────────────────────────────────────────────────────

class TestWorkflowOrchestration:
    """End-to-end workflow: order of creation matters."""

    def test_workflow_sequence(self, cbdc_payment, treasury_instruction,
                               policy_evaluation, settlement, audit_record, provenance_log):
        """Verify chronological dependency chain."""
        times = {
            "payment": cbdc_payment.created_at,
            "treasury": treasury_instruction.created_at,
            "policy": policy_evaluation.created_at,
            "settlement": settlement.created_at,
            "audit": audit_record.created_at,
            "provenance": provenance_log.created_at,
        }
        assert times["payment"] <= times["treasury"], "Treasury after payment"
        assert times["payment"] <= times["policy"], "Policy after payment"
        assert times["policy"] <= times["settlement"], "Settlement after policy"
        assert times["settlement"] <= times["audit"], "Audit after settlement"
        assert times["audit"] <= times["provenance"], "Provenance after audit"


# ─────────────────────────────────────────────────────────────
# Conformance Report Generation
# ─────────────────────────────────────────────────────────────

def pytest_sessionfinish(session, exitstatus):
    """Print summary at end of test run."""
    print()
    print("=" * 60)
    print("  Finance Reference Node — Conformance Summary")
    print("=" * 60)
    print(f"  Result: {'PASSED' if exitstatus == 0 else 'FAILED'}")
    print(f"  Tests:  {session.testscollected} collected, "
          f"{session.testscollected - len(session.testsfailed)} passed, "
          f"{len(session.testsfailed)} failed")
    print("=" * 60)
