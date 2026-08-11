"""MOR-009: Evidence verification.

A third party must be able to verify an evidence package using only the package
and the relevant public keys — no access to HPE Morpheus required.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC
from evidence.evidence_verifier import EvidenceVerifier, package_hash
from provenance.morpheus_provenance_chain import resolve_key_from

pytestmark = pytest.mark.level("L3")


def test_package_verifies_without_morpheus(client, make_request, quota, agent_keys, node_keys):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    package = client.last_package
    ok, reasons = EvidenceVerifier().verify(
        package,
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}),
        node_keys["public"],
    )
    assert ok
    assert any("evidence verified" in r for r in reasons)


def test_verify_dict_wrapper(client, make_request, quota, agent_keys, node_keys):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    registry = {"agent://ml-platform": agent_keys["public"]}
    ok, _ = EvidenceVerifier().verify_dict(
        client.last_package.to_dict(), registry, node_keys["public"]
    )
    assert ok


def test_wrong_node_key_rejects(client, make_request, quota, agent_keys, node_keys):
    from crypto import generate_keypair

    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    _, other_public = generate_keypair()
    ok, reasons = EvidenceVerifier().verify(
        client.last_package,
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}),
        other_public,
    )
    assert ok is False
    assert any("signature" in r for r in reasons)


def test_package_hash_is_stable(client, make_request, quota):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    package = client.last_package
    assert package_hash(package) == package_hash(package)
    assert len(package_hash(package)) == 64
