"""Conformance tests for SovereignStack URI scheme parsing and object model."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdks", "python"))

import json
import pytest
from sovereignstack.uri import parse_uri, UriScheme, ParsedUri
from sovereignstack.objects import (
    SovereignObject, Payment, Settlement, Treasury,
    PolicyEvaluation, AuditRecord, ProvenanceLog,
)


class TestUriParsing:
    """RFC-0001 / RFC-0010: URI scheme parsing conformance."""

    def test_parse_payment_uri(self):
        p = parse_uri("payment://cbdc/ecb/pacs008-001")
        assert p.scheme == UriScheme.PAYMENT
        assert p.authority == "cbdc"
        assert p.path == "ecb/pacs008-001"

    def test_parse_settlement_uri(self):
        p = parse_uri("settlement://dvp/trade-88")
        assert p.scheme == UriScheme.SETTLEMENT
        assert p.authority == "dvp"
        assert p.path == "trade-88"

    def test_parse_treasury_uri(self):
        p = parse_uri("treasury://acme/main-usd")
        assert p.scheme == UriScheme.TREASURY
        assert p.authority == "acme"
        assert p.path == "main-usd"

    def test_parse_agent_uri(self):
        p = parse_uri("agent://reasoning/math")
        assert p.scheme == UriScheme.AGENT
        assert p.authority == "reasoning"
        assert p.path == "math"

    def test_parse_evidence_uri(self):
        p = parse_uri("evidence://audit/tx-abc123")
        assert p.scheme == UriScheme.EVIDENCE
        assert p.authority == "audit"
        assert p.path == "tx-abc123"

    def test_parse_person_uri(self):
        p = parse_uri("person://alice-j-doe")
        assert p.scheme == UriScheme.PERSON
        assert p.authority == "alice-j-doe"

    def test_parse_company_uri(self):
        p = parse_uri("company://acme-corp")
        assert p.scheme == UriScheme.COMPANY
        assert p.authority == "acme-corp"

    def test_parse_economy_uri(self):
        p = parse_uri("economy://eu/digital-euro")
        assert p.scheme == UriScheme.ECONOMY
        assert p.authority == "eu"
        assert p.path == "digital-euro"

    def test_parse_invalid_uri_no_scheme(self):
        with pytest.raises(ValueError, match="missing ://"):
            parse_uri("invalid-uri")

    def test_parse_invalid_scheme(self):
        with pytest.raises(ValueError, match="Unknown URI scheme"):
            parse_uri("nonexistent://foo")

    def test_all_economy_schemes_parse(self):
        economy_schemes = [
            "economy://x", "asset://x", "payment://x", "treasury://x",
            "market://x", "risk://x", "insurance://x", "settlement://x",
            "exchange://x", "tax://x", "derivative://x", "account://x",
        ]
        for uri in economy_schemes:
            p = parse_uri(uri)
            assert p.authority == "x"

    def test_all_twin_schemes_parse(self):
        twin_schemes = [
            "person://x", "company://x", "bank://x", "hospital://x",
            "portfolio://x", "fund://x", "bond://x", "stock://x",
            "factory://x", "vehicle://x", "city://x",
        ]
        for uri in twin_schemes:
            p = parse_uri(uri)
            assert p.authority == "x"


class TestObjectModel:
    """RFC-0001: Object model conformance — sign, serialize, roundtrip."""

    def test_payment_creation(self):
        payment = Payment.create(
            uri="payment://cbdc/test-001",
            sender="account://bank/main",
            receiver="account://acme/op",
            amount=100000,
            currency="EUR",
        )
        assert payment.kind == "payment"
        assert payment.data["amount"]["value"] == 100000
        assert payment.data["status"] == "initiated"

    def test_object_sign(self):
        obj = SovereignObject(uri="test://x", kind="test", data={"a": 1})
        obj.sign("signer://test")
        assert obj.signature.startswith("ed25519:")

    def test_json_roundtrip(self):
        payment = Payment.create(
            uri="payment://test/roundtrip",
            sender="account://a", receiver="account://b",
            amount=500, currency="USD",
        )
        payment.sign("signer://test")
        json_str = payment.to_json()
        restored = SovereignObject.from_json(json_str)
        assert restored.uri == payment.uri
        assert restored.kind == payment.kind
        assert restored.data == payment.data

    def test_settlement_creation(self):
        s = Settlement.create(
            uri="settlement://dvp/test",
            payment_ref="payment://test/001",
            method="delivery_vs_payment",
            asset="asset://cbdc/eur",
            amount={"value": 100000, "currency": "EUR"},
        )
        assert s.data["status"] == "pending"

    def test_treasury_creation(self):
        t = Treasury.create(
            uri="treasury://acme/test",
            treasury_account="treasury://acme/main",
            action="credit_received",
            amount={"value": 50000, "currency": "USD"},
            approved_by="person://alice",
        )
        assert t.data["action"] == "credit_received"

    def test_audit_record_chain(self):
        chain = ["payment://x", "settlement://x", "evidence://x"]
        audit = AuditRecord.create(
            uri="evidence://audit/test",
            chain=chain,
            total_amount={"value": 1000, "currency": "EUR"},
            auditor="agent://audit-01",
        )
        assert len(audit.data["transaction_chain"]) == 3
        assert audit.data["chain_hash"] is not None

    def test_provenance_log(self):
        objs = [
            SovereignObject(uri="a://1", kind="a", data={}),
            SovereignObject(uri="b://2", kind="b", data={}),
        ]
        log = ProvenanceLog.create(uri="chain://test", objects=objs, signer="agent://01")
        assert log.data["total_entries"] == 2
        assert log.signature.startswith("ed25519:")


class TestPolicyEvaluation:
    """RFC-0020: Policy engine evaluation conformance."""

    def test_policy_checks(self):
        policy = PolicyEvaluation.create(
            uri="policy://engine/test",
            payment_ref="payment://test/001",
            checks={"aml": "passed", "kyc": "passed"},
            overall_result="approved",
            score=0.95,
            evaluator="policy://engine/aml-v3",
        )
        assert policy.data["overall_result"] == "approved"
        assert policy.data["checks"]["aml"] == "passed"
