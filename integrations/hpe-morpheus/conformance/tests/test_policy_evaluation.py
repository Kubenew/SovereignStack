"""MOR-004: Policy evaluation.

Policies translate to ALLOW/DENY per rule. Mixed policy results resolve to
DENY + escalate (RFC-0075 safe halt) — the engine never guesses.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC, OVERSIZED_SPEC, PROD_NET_DEV_ENV
from adapter.policy_translator import PolicyEvaluator

pytestmark = pytest.mark.level("L3")


def test_compliant_spec_allowed(policies, quota):
    allow, reasons, violations, escalate = policies.evaluate(COMPLIANT_SPEC, quota)
    assert allow is True
    assert not violations
    assert not escalate


def test_oversized_spec_denied(policies, quota):
    allow, reasons, violations, escalate = policies.evaluate(OVERSIZED_SPEC, quota)
    assert allow is False
    assert any("VM-CPU-MAX" in v for v in violations)
    assert any("NET-APPROVED" in v for v in violations)
    assert escalate is False


def test_missing_quota_denied(policies):
    allow, _, violations, _ = policies.evaluate(COMPLIANT_SPEC, {})
    assert allow is False
    assert any("quota" in v for v in violations)


def test_when_condition_isolates_production_network(policies, quota):
    allow, _, violations, _ = policies.evaluate(PROD_NET_DEV_ENV, quota)
    assert allow is False
    assert any("NET-PROD-ISOLATION" in v for v in violations)


def test_policy_conflict_safe_halts_and_escalates():
    evaluator = PolicyEvaluator()
    evaluator.policies.append(
        {
            "policy_id": "policy://test/allow",
            "rules": [{"id": "T-ALLOW", "target": "spec.cpu", "op": "le", "value": 16}],
        }
    )
    evaluator.policies.append(
        {
            "policy_id": "policy://test/deny",
            "rules": [{"id": "T-DENY", "target": "spec.cpu", "op": "le", "value": 4}],
        }
    )
    allow, reasons, _, escalate = evaluator.evaluate({"cpu": 8})
    assert allow is False
    assert escalate is True
    assert any("safe halt" in r for r in reasons)


def test_no_policies_denies_by_default():
    evaluator = PolicyEvaluator()
    allow, _, _, escalate = evaluator.evaluate({"cpu": 8})
    assert allow is False
    assert escalate is True
