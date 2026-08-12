"""MOR-008: Evidence package.

Each governed action produces a self-describing, signed package that embeds the
decision, the checks that ran, and the provenance chain — persistable and
portable for external audit.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC
from evidence.evidence_generator import EvidencePackage

pytestmark = pytest.mark.level("L3")


def test_governed_allow_produces_package(client, make_request, quota):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    package = client.last_package
    assert package is not None
    assert package.decision == "ALLOW"
    assert package.conformance_profile == "oasa-profile://morpheus-core/v0.1"
    assert package.signature is not None
    assert len(package.chain["entries"]) >= 1


def test_package_roundtrip(client, make_request, quota, tmp_path):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    package = client.last_package
    path = package.save(str(tmp_path / "evidence.json"))
    loaded = EvidencePackage.load(path)
    assert loaded.package_id == package.package_id
    assert loaded.decision == package.decision
    assert loaded.chain == package.chain
    assert loaded.metadata == package.metadata


def test_package_embeds_checks(client, make_request, quota):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    checks = client.last_package.checks
    kinds = {c["check"] for c in checks}
    assert {"identity", "capability", "policy"} <= kinds
