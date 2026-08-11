"""Conformance test vectors — the shipped ``test-vectors/*.json`` files must
hold against the governed pipeline exactly as declared.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from _shared import AGENT_URI, COMPUTE_PROVISION
from api.morpheus_schemas import GovernedRequest
from crypto import canonical_json, sign
from provenance.morpheus_provenance_chain import ProvenanceChain, resolve_key_from

pytestmark = pytest.mark.level("L3")

VECTORS = Path(__file__).resolve().parents[1] / "test-vectors"


def _request(input_: dict, agent_private_key: str) -> GovernedRequest:
    request = GovernedRequest(
        action=input_["action"],
        agent_uri=input_["agent_uri"],
        capability=input_["capability"],
        spec=input_["spec"],
        nonce=uuid.uuid4().hex,
        environment=input_["spec"].get("environment"),
    )
    request.signature = sign(canonical_json(request.message()), agent_private_key)
    return request


def test_provision_vm_allow_vector(client, make_request, agent_keys, node_keys, quota):
    vector = json.loads((VECTORS / "provision-vm.json").read_text(encoding="utf-8"))
    decision = client.govern(_request(vector["input"], agent_keys["private"]), quota=quota)
    assert decision.decision == vector["expected"]["decision"]
    assert decision.morpheus_called == vector["expected"]["morpheus_called"]
    assert client.last_package is not None
    ok, _ = client.chain.verify(
        resolve_key_from({AGENT_URI: agent_keys["public"]}), node_keys["public"]
    )
    assert ok


def test_provision_vm_deny_vector(client, agent_keys, quota):
    vector = json.loads((VECTORS / "deny-vm.json").read_text(encoding="utf-8"))
    decision = client.govern(_request(vector["input"], agent_keys["private"]), quota=quota)
    assert decision.decision == vector["expected"]["decision"]
    assert decision.reason == vector["expected"]["reason"]
    assert decision.morpheus_called == vector["expected"]["morpheus_called"]


def test_tamper_detection_vector(agent_keys, node_keys):
    vector = json.loads((VECTORS / "tamper-detection.json").read_text(encoding="utf-8"))
    from evidence.evidence_verifier import EvidenceVerifier
    from provenance.morpheus_provenance_chain import ProvenanceEntry

    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    spec = vector["input"]["spec"]
    first = chain.append(
        ProvenanceEntry(
            seq=1,
            action="provision-vm",
            agent_uri=AGENT_URI,
            object_uri="vm://morpheus/vm-1",
            decision="ALLOW",
            detail=spec,
        ),
        private_key_hex=node_keys["private"],
    )
    chain.append(
        ProvenanceEntry(
            seq=2,
            action="provision-vm",
            agent_uri=AGENT_URI,
            object_uri="vm://morpheus/vm-2",
            decision="ALLOW",
            detail=spec,
            prev_hash=first.hash(),
        ),
        private_key_hex=node_keys["private"],
    )
    # Apply the declared attack: post-hoc modification of a recorded entry
    attack = vector["attack"]
    chain.entries[1].detail[attack["modify"]] = attack["to"]

    ok, _ = chain.verify(resolve_key_from({AGENT_URI: agent_keys["public"]}), node_keys["public"])
    assert ok == vector["expected"]["verified"]
