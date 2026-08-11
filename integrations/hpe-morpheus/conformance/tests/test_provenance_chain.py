"""MOR-005: Provenance chain.

Every governed action appends a content-hashed, signed entry chained by
``prev_hash``. The chain is tamper-evident and independently verifiable.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC
from provenance.morpheus_provenance_chain import (
    ChainLinkError,
    ProvenanceChain,
    ProvenanceEntry,
    resolve_key_from,
)

pytestmark = pytest.mark.level("L3")


def _entry(seq: int, prev_hash=None, detail: dict | None = None) -> ProvenanceEntry:
    return ProvenanceEntry(
        seq=seq,
        action="provision-vm",
        agent_uri="agent://ml-platform",
        object_uri=f"vm://morpheus/vm-{seq}",
        decision="ALLOW",
        detail=detail or {"memory_gb": 32},
        prev_hash=prev_hash,
    )


def test_chain_links_and_verifies(agent_keys, node_keys):
    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    first = chain.append(_entry(1), private_key_hex=node_keys["private"])
    second = chain.append(
        _entry(2, prev_hash=first.hash()), private_key_hex=node_keys["private"]
    )
    assert first.hash() != second.hash()
    ok, reasons = chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok
    assert len(chain.entries) == 2


def test_broken_linkage_rejected(agent_keys, node_keys):
    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    chain.append(_entry(1), private_key_hex=node_keys["private"])
    with pytest.raises(ChainLinkError):
        chain.append(_entry(2, prev_hash="0000"), private_key_hex=node_keys["private"])


def test_governed_actions_grow_the_chain(client, make_request, quota):
    before = len(client.chain.entries)
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    assert len(client.chain.entries) == before + 1
    entry = client.chain.entries[-1]
    assert entry.action == "provision-vm"
    assert entry.signature is not None
