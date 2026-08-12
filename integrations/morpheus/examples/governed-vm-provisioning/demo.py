"""End-to-end demo: governing HPE Morpheus VM provisioning with SovereignStack.

Runs the full contract against the bundled mock Morpheus API:

    identity -> capability -> policy -> decision -> Morpheus -> provenance -> evidence

Requests that violate policy are DENIED *before* Morpheus is ever called, and
both paths produce signed, verifiable evidence.

Usage:
    python examples/governed-vm-provisioning/demo.py
"""

from __future__ import annotations

import json
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
INTEGRATION = os.path.dirname(os.path.dirname(HERE))
if INTEGRATION not in sys.path:
    sys.path.insert(0, INTEGRATION)

import uuid  # noqa: E402

from adapter.capability_mapper import CapabilityMapper  # noqa: E402
from adapter.identity_mapper import IdentityMapper  # noqa: E402
from adapter.policy_translator import PolicyEvaluator  # noqa: E402
from api.morpheus_client import GovernedClient  # noqa: E402
from api.morpheus_mock import make_server  # noqa: E402
from api.morpheus_schemas import GovernedRequest  # noqa: E402
from crypto import canonical_json, generate_keypair, sign  # noqa: E402
from evidence.evidence_verifier import EvidenceVerifier, package_hash  # noqa: E402
from provenance.morpheus_provenance_chain import (  # noqa: E402
    ProvenanceChain,
    resolve_key_from,
)

POLICY_DIR = os.path.join(INTEGRATION, "policies")

ALLOW_SPEC = {
    "cpu": 8,
    "memory_gb": 32,
    "network": "prod-vlan-42",
    "image": "ubuntu-22.04-lts",
    "environment": "production",
}
DENY_SPEC = {
    "cpu": 64,
    "memory_gb": 512,
    "network": "unapproved-network",
    "image": "ubuntu-22.04-lts",
    "environment": "production",
}
QUOTA = {"cpu_remaining": 16, "memory_gb_remaining": 64, "running_vms": 3}


def _rule(text: str = "") -> str:
    return "=" * 70 if not text else "=" * 3 + " " + text + " " + "=" * (70 - len(text) - 4)


def _run(
    client: GovernedClient,
    agent_private_key: str,
    spec: dict,
    label: str,
) -> object:
    request = GovernedRequest(
        action="provision-vm",
        agent_uri="agent://ml-platform",
        capability="capability://compute/provision",
        spec=spec,
        nonce=uuid.uuid4().hex,
        environment=spec.get("environment"),
    )
    request.signature = sign(canonical_json(request.message()), agent_private_key)
    print(f"{_rule(label)}\n")
    print("  Request:")
    print("    " + json.dumps(request.message(), indent=4).replace("\n", "\n    "))
    decision = client.govern(request, quota=QUOTA)
    print("\n  Decision: " + decision.decision)
    print("  Reason:   " + str(decision.reason))
    print("  Morpheus: " + ("CALLED -> " + decision.vm_id if decision.morpheus_called else "never called"))
    print("\n  Checks:")
    for check in decision.checks:
        print(f"    {check['check']:<12} {check['result']:<7} {check['detail']}")
    return decision


def main() -> int:
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_address[1]}"

    print(_rule("SovereignStack x HPE Morpheus - governed VM provisioning demo"))
    print("\n  Mock Morpheus API: " + endpoint)

    # 1. Identity: register the demo agent and bind it to a Morpheus user
    agent_private, agent_public = generate_keypair()
    identity = IdentityMapper()
    identity.register("agent://ml-platform", agent_public)
    identity.bind("ml-service-account", "agent://ml-platform")

    # 2. Capability: the agent may provision compute (role-derived grant)
    capabilities = CapabilityMapper()
    capabilities.grant_role("agent://ml-platform", "ml-engineer")

    # 3. Policy: load the governance catalogs
    policies = PolicyEvaluator(POLICY_DIR)

    # 4. Provenance + evidence
    node_private, node_public = generate_keypair()
    chain = ProvenanceChain(target="chain://morpheus/ml-platform")
    client = GovernedClient(
        endpoint,
        identity,
        capabilities,
        policies,
        chain,
        node_private,
        node_public,
    )

    allow = _run(client, agent_private, ALLOW_SPEC, "request 1: compliant VM (expect ALLOW)")
    deny = _run(client, agent_private, DENY_SPEC, "request 2: oversized VM on unapproved network (expect DENY)")

    # 5. Verify the audit trail independently
    print(_rule("verification: provenance + evidence"))
    resolver = resolve_key_from({"agent://ml-platform": agent_public})
    chain_ok, chain_reasons = chain.verify(resolver, node_public)
    print("\n  provenance chain:  " + ("VERIFIED" if chain_ok else "FAILED"))
    for reason in chain_reasons:
        print("    - " + reason)

    verifier = EvidenceVerifier()
    last = client.last_package
    pkg_ok, pkg_reasons = verifier.verify(last, resolver, node_public)
    print("\n  evidence package:  " + ("VERIFIED" if pkg_ok else "FAILED"))
    for reason in pkg_reasons:
        print("    - " + reason)
    print(f"\n  package hash: {package_hash(last)}")
    print(f"  decision:    {last.decision}")
    print(f"  profile:     {last.conformance_profile}")

    print(_rule("summary"))
    print(f"\n  ALLOW path:  decision=ALLOW, morpheus_called={allow.morpheus_called}")
    print(f"  DENY path:   decision=DENY,  morpheus_called={deny.morpheus_called}")
    print(f"  mock actions recorded: {len(server.actions)} (only the ALLOW should reach Morpheus)")

    assert allow.decision == "ALLOW" and allow.morpheus_called
    assert deny.decision == "DENY" and not deny.morpheus_called
    assert len(server.actions) == 1, "Morpheus must not be called for DENIED requests"
    assert chain_ok and pkg_ok
    print("\n  Demo PASSED - governance pipeline verified end to end.\n")
    server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
