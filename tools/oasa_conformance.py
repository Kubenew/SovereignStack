#!/usr/bin/env python3
"""
OASA Conformance CLI Runner
Specification: OASA v0.6 Governed Autonomous Action
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from conformance.core_engine import CoreEngine
from integrations.morpheus.adapter.morpheus_adapter import MorpheusAdapter
import conformance.tests.test_v06_conformance as suite


def run_conformance(profile_path: str, output_file: str = "oasa-conformance-report.json") -> bool:
    print("=" * 64)
    print(f"OASA CONFORMANCE HARNESS — Profile: {profile_path}")
    print("=" * 64)

    engine = CoreEngine()
    adapter = MorpheusAdapter()
    engine.register_adapter("morpheus", adapter)
    # engine and adapter are registered; used implicitly via engine below

    tests = [
        ("AUTH-001", "AuthorizationPrecedesExecution", suite.test_authorization_precedes_execution),
        ("AUTH-002", "TestUnauthorizedActionNeverReachesProvider", suite.test_unauthorized_action_never_reaches_provider),
        ("AUTH-003", "TestAuthorizationTokenExpires", suite.test_authorization_token_expires),
        ("AUTH-004", "TestAuthorizationTokenCannotBeReplayed", suite.test_authorization_token_cannot_be_replayed),
        ("AUTH-005", "TestCapabilityCannotBeEscalated", suite.test_capability_cannot_be_escalated),
        ("AUTH-006", "TestTargetCannotBeChangedAfterAuthorization", suite.test_target_cannot_be_changed_after_authorization),
        ("ENV-001",  "TestActionEnvelopeHasUniqueId", suite.test_action_envelope_has_unique_id),
        ("ENV-002",  "TestActorIsAttributable", suite.test_actor_is_attributable),
        ("ENV-003",  "TestCapabilityIsExplicit", suite.test_capability_is_explicit),
        ("ENV-004",  "TestTargetIsExplicit", suite.test_target_is_explicit),
        ("DEL-001",  "TestDelegationChainIsPreserved", suite.test_delegation_chain_is_preserved),
        ("DEL-002",  "TestInvalidDelegationIsRejected", suite.test_invalid_delegation_is_rejected),
        ("PROV-001", "TestProviderActionIdIsLinked", suite.test_provider_action_id_is_linked),
        ("EVID-001", "TestAuthorizedActionProducesVerifiableEvidence", suite.test_authorized_action_produces_verifiable_evidence),
        ("EVID-002", "TestTamperedEvidenceFailsVerification", suite.test_tampered_evidence_fails_verification),
    ]

    results = []
    all_passed = True

    for test_id, name, fn in tests:
        # Re-initialize clean adapter per test to ensure isolated counts
        clean_adapter = MorpheusAdapter()
        engine.register_adapter("morpheus", clean_adapter)
        test_setup = (engine, clean_adapter)

        try:
            fn(test_setup)
            print(f"  [PASS] {test_id:<8} {name}")
            results.append({"id": test_id, "name": name, "status": "PASS"})
        except Exception as e:
            print(f"  [FAIL] {test_id:<8} {name} — Error: {e}")
            results.append({"id": test_id, "name": name, "status": "FAIL", "error": str(e)})
            all_passed = False

    total = len(tests)
    passed = sum(1 for r in results if r["status"] == "PASS")
    status_label = "OASA-CONFORMANT" if all_passed else "NON-CONFORMANT"

    print("-" * 64)
    print(f"Summary: {passed}/{total} Passed ({(passed/total)*100:.0f}%)")
    print(f"STATUS: {status_label}")
    print("-" * 64)

    report = {
        "profile": profile_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": total,
        "passed_tests": passed,
        "status": status_label,
        "tests": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Attestation report saved to: {output_file}")
    print("=" * 64)
    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OASA Conformance Test Harness")
    parser.add_argument("--profile", default="profiles/core/0.1.yaml", help="Path to profile YAML")
    parser.add_argument("--output", default="oasa-conformance-report.json", help="Output report path")
    args = parser.parse_args()

    success = run_conformance(args.profile, args.output)
    sys.exit(0 if success else 1)
