"""Policy translation — policy YAML catalogs into an evaluation engine.

Policies are loaded from ``policies/`` and evaluated over a request spec. Each
policy yields ALLOW or DENY; if policies disagree (mixed result), the engine
applies the RFC-0075 safe-halt rule: DENY and escalate to a human. It never
guesses.
"""

from __future__ import annotations

import copy
import glob
import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs pyyaml
    yaml = None


@dataclass
class PolicyResult:
    allow: bool
    policy_id: str
    reasons: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    passed_targets: list = field(default_factory=list)
    violated_targets: list = field(default_factory=list)
    escalate: bool = False


def _get_path(obj: dict, dotted: str) -> Optional[object]:
    current = obj
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _check_rule(rule: dict, spec: dict, quota: Optional[dict]) -> tuple[bool, Optional[str]]:
    target = rule["target"]
    op = rule["op"]
    expected = rule["value"]
    if target.startswith("spec."):
        actual = _get_path(spec, target[len("spec."):])
    else:
        actual = _get_path(quota or {}, target.replace("quota.", ""))
    if actual is None:
        return False, f"{target} is missing"
    if op == "le":
        ok = actual <= expected
    elif op == "ge":
        ok = actual >= expected
    elif op == "lt":
        ok = actual < expected
    elif op == "gt":
        ok = actual > expected
    elif op == "eq":
        ok = actual == expected
    elif op == "in":
        ok = actual in expected
    elif op == "not_in":
        ok = actual not in expected
    else:
        return False, f"unsupported op {op}"
    if ok:
        return True, None
    return False, rule.get("message", f"rule {rule['id']} failed")


class PolicyEvaluator:
    """Loads policy YAML catalogs and evaluates them against a request."""

    def __init__(self, policy_dir: Optional[str] = None) -> None:
        self.policy_dir = policy_dir
        self.policies: list[dict] = []
        if policy_dir is not None:
            self.load_dir(policy_dir)

    def load_dir(self, policy_dir: str) -> list:
        for path in sorted(glob.glob(os.path.join(policy_dir, "*.yaml"))):
            self.load_file(path)
        return self.policies

    def load_file(self, path: str) -> dict:
        if yaml is None:
            raise RuntimeError("pyyaml required to load policy catalogs")
        with open(path, "r", encoding="utf-8") as fh:
            policy = yaml.safe_load(fh)
        self.policies.append(policy)
        return policy

    def evaluate_policy(
        self, policy: dict, spec: dict, quota: Optional[dict] = None
    ) -> PolicyResult:
        """Evaluate one policy. ALLOW only if every applicable rule passes."""
        result = PolicyResult(allow=True, policy_id=policy["policy_id"])
        for rule in policy.get("rules", []):
            if rule.get("when"):
                if not self._when_matches(rule["when"], spec):
                    continue
            ok, message = _check_rule(rule, spec, quota)
            if ok:
                result.passed_targets.append(rule["target"])
            else:
                result.allow = False
                result.violated_targets.append(rule["target"])
                result.violations.append(rule["id"] + (f": {message}" if message else ""))
        if result.allow:
            result.reasons.append(f"{policy['policy_id']}: ALLOW")
        else:
            result.reasons.append(f"{policy['policy_id']}: DENY")
        return result

    @staticmethod
    def _when_matches(condition: dict, spec: dict) -> bool:
        """Minimal `when` support.

        A key ending in ``_prefix`` matches when the underlying spec field
        starts with the given value (e.g. ``network_prefix: prod`` checks
        ``spec.network`` starts with ``prod``). Other keys match exactly.
        """
        for field, value in condition.items():
            if isinstance(value, str) and field.endswith("_prefix"):
                actual_field = field[: -len("_prefix")]
                actual = _get_path(spec, actual_field.replace("spec.", ""))
                if not (actual and str(actual).startswith(value)):
                    return False
                continue
            actual = _get_path(spec, field.replace("spec.", ""))
            if actual != value:
                return False
        return True

    def evaluate(
        self, spec: dict, quota: Optional[dict] = None
    ) -> tuple[bool, list[str], list[str], bool]:
        """Evaluate all loaded policies with RFC-0075 conflict resolution.

        Returns ``(allow, reasons, violations, escalate)``. Any DENY denies the
        request. A conflict — the same target field simultaneously satisfied and
        violated by different rules — resolves to DENY + escalate (safe halt).
        The engine never guesses.
        """
        if not self.policies:
            return False, ["no policies loaded - denying by default"], [], True
        decisions = [self.evaluate_policy(p, spec, quota) for p in self.policies]
        reasons: list[str] = []
        violations: list[str] = []
        for d in decisions:
            reasons.extend(d.reasons)
            violations.extend(d.violations)

        passed = set().union(*(set(d.passed_targets) for d in decisions))
        violated = set().union(*(set(d.violated_targets) for d in decisions))
        conflict = passed & violated
        if conflict:
            reasons.append(
                f"policy conflict on {sorted(conflict)} - safe halt, human escalation"
            )
            return False, reasons, violations, True
        if any(not d.allow for d in decisions):
            return False, reasons, violations, False
        return True, reasons, violations, False
