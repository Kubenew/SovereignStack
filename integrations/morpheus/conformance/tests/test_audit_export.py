"""MOR-010: Audit export.

Evidence packages aggregate into a single audit bundle an external auditor can
consume, including an independent re-verification of every package.
"""

from __future__ import annotations

import json

import pytest

from _shared import COMPLIANT_SPEC, OVERSIZED_SPEC
from assurance import build_audit_report, save_audit
from provenance.morpheus_provenance_chain import resolve_key_from

pytestmark = pytest.mark.level("L3")


def test_audit_report_summary(client, make_request, quota):
    before = len(client._packages)
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    client.govern(make_request(OVERSIZED_SPEC), quota=quota)
    packages = client._packages[before:]
    report = build_audit_report(packages)
    assert report["summary"]["total"] == 2
    assert report["summary"]["allow"] == 1
    assert report["summary"]["deny"] == 1
    assert len(report["evidence"]) == 2
    assert report["report"]["profile"] == "oasa-profile://morpheus-core/v0.1"


def test_audit_report_reverifies_packages(client, make_request, quota, agent_keys, node_keys):
    before = len(client._packages)
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    packages = client._packages[before:]
    report = build_audit_report(
        packages,
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}),
        node_keys["public"],
    )
    assert report["summary"]["verified"] == 1
    assert report["evidence"][0]["verified"] is True


def test_save_audit_writes_json(client, make_request, quota, tmp_path, agent_keys, node_keys):
    before = len(client._packages)
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    packages = client._packages[before:]
    path = save_audit(
        str(tmp_path / "audit.json"),
        packages,
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}),
        node_keys["public"],
    )
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["summary"]["total"] == 1
    assert data["evidence"][0]["decision"] == "ALLOW"
