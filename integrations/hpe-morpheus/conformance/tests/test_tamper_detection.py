"""MOR-007: Tamper detection.

Any post-hoc modification of a recorded entry — detail, linkage, or signature —
must break chain verification at the exact entry it occurred.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC
from provenance.morpheus_provenance_chain import ProvenanceChain, resolve_key_from

pytestmark = pytest.mark.level("L3")


def _chain(agent_keys, node_keys) -> ProvenanceChain:
    from provenance.morpheus_provenance_chain import ProvenanceEntry

    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    chain.append(
        ProvenanceEntry(
            seq=1,
            action="provision-vm",
            agent_uri="agent://ml-platform",
            object_uri="vm://morpheus/vm-1",
            decision="ALLOW",
            detail={"memory_gb": 32},
        ),
        private_key_hex=node_keys["private"],
    )
    return chain


def test_detail_tamper_detected(agent_keys, node_keys):
    chain = _chain(agent_keys, node_keys)
    chain.entries[0].detail["memory_gb"] = 512  # tamper after signing
    ok, reasons = chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok is False
    assert any("tampered" in r for r in reasons)


def test_linkage_tamper_detected(agent_keys, node_keys):
    from provenance.morpheus_provenance_chain import ProvenanceEntry

    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    first = chain.append(
        ProvenanceEntry(
            seq=1,
            action="provision-vm",
            agent_uri="agent://ml-platform",
            object_uri="vm://morpheus/vm-1",
            decision="ALLOW",
            detail={"memory_gb": 32},
        ),
        private_key_hex=node_keys["private"],
    )
    second = chain.append(
        ProvenanceEntry(
            seq=2,
            action="provision-vm",
            agent_uri="agent://ml-platform",
            object_uri="vm://morpheus/vm-2",
            decision="ALLOW",
            detail={"memory_gb": 32},
            prev_hash=first.hash(),
        ),
        private_key_hex=node_keys["private"],
    )
    second.prev_hash = first.hash()[:-2] + "00"  # corrupt linkage
    ok, reasons = chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok is False
    assert any("linkage" in r for r in reasons)


def test_signature_tamper_detected(agent_keys, node_keys):
    chain = _chain(agent_keys, node_keys)
    chain.entries[0].signature = "00" * 64
    ok, reasons = chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok is False
    assert any("signature" in r for r in reasons)


def test_reference_vector_tamper_contract(agent_keys, node_keys, client, make_request, quota):
    """Governed allow -> mutate evidence -> verifier must reject."""
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    package = client.last_package
    chain = ProvenanceChain.from_dict(package.chain)
    chain.entries[-1].detail["memory_gb"] = 512
    package.chain = chain.to_dict()
    from evidence.evidence_verifier import EvidenceVerifier

    ok, reasons = EvidenceVerifier().verify(
        package,
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}),
        node_keys["public"],
    )
    assert ok is False
    assert any(
        "signature" in r or "tampered" in r or "linkage" in r for r in reasons
    )
