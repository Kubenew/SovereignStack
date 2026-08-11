"""MOR-006: Event integrity.

Asynchronous Morpheus events (provisioned, configured, deleted) are content
hashed and chained, so infrastructure state changes outside a direct request
remain part of the auditable record.
"""

from __future__ import annotations

import pytest

from _shared import COMPLIANT_SPEC
from adapter.event_listener import EventListener
from provenance.morpheus_provenance_chain import ProvenanceChain, resolve_key_from

pytestmark = pytest.mark.level("L3")


def test_event_append_and_verify(agent_keys, node_keys):
    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    listener = EventListener(node_keys["public"])
    recorded = []
    listener.on_event(lambda entry: recorded.append(entry))

    listener.record(
        chain,
        action="provisioned",
        object_uri="vm://morpheus/vm-1001",
        detail={"status": "running", "node": "compute-1"},
        signer_private_key_hex=node_keys["private"],
    )
    assert len(recorded) == 1
    assert chain.entries[-1].object_uri == "vm://morpheus/vm-1001"

    ok, reasons = chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok
    assert any("event://morpheus" == e.agent_uri for e in chain.entries)


def test_event_links_after_governed_entry(client, node_keys, agent_keys, make_request, quota):
    client.govern(make_request(COMPLIANT_SPEC), quota=quota)
    listener = EventListener(node_keys["public"])
    listener.record(
        client.chain,
        action="configured",
        object_uri="vm://morpheus/vm-1002",
        detail={"settings": {"flavor": "c8"}},
        signer_private_key_hex=node_keys["private"],
    )
    ok, _ = client.chain.verify(
        resolve_key_from({"agent://ml-platform": agent_keys["public"]}), node_keys["public"]
    )
    assert ok
