"""Pytest config for the OASA-MORPHEUS-CORE-0.1 conformance suite.

Provides the shared governance stack (identity, capability, policy, chain,
client), a mock Morpheus server, and the ``--report-dir`` report fixtures used
across the finance conformance suite.
"""

from __future__ import annotations

import json
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

INTEGRATION = Path(__file__).resolve().parents[2]
if str(INTEGRATION) not in sys.path:
    sys.path.insert(0, str(INTEGRATION))

from adapter.capability_mapper import CapabilityMapper  # noqa: E402
from adapter.identity_mapper import IdentityMapper  # noqa: E402
from adapter.policy_translator import PolicyEvaluator  # noqa: E402
from api.morpheus_client import GovernedClient  # noqa: E402
from api.morpheus_mock import make_server  # noqa: E402
from api.morpheus_schemas import GovernedRequest  # noqa: E402
from crypto import canonical_json, generate_keypair, sign  # noqa: E402
from provenance.morpheus_provenance_chain import ProvenanceChain  # noqa: E402

POLICY_DIR = INTEGRATION / "policies"


def pytest_addoption(parser):
    parser.addoption(
        "--report-dir",
        action="store",
        default="reports",
        help="Directory for conformance reports",
    )


@pytest.fixture(scope="session")
def report_dir(request) -> Path:
    return Path(request.config.getoption("--report-dir"))


@pytest.fixture(scope="session")
def save_report(report_dir):
    """Factory fixture: save_report(report_name, data) writes JSON report."""
    report_dir.mkdir(parents=True, exist_ok=True)

    def _save(name: str, data: dict) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = report_dir / f"{name}-{ts}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    return _save


@pytest.fixture(scope="session")
def morpheus_server():
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


@pytest.fixture(scope="session")
def endpoint(morpheus_server) -> str:
    return f"http://127.0.0.1:{morpheus_server.server_address[1]}"


@pytest.fixture(scope="session")
def agent_keys():
    private, public = generate_keypair()
    return {"private": private, "public": public}


@pytest.fixture(scope="session")
def node_keys():
    private, public = generate_keypair()
    return {"private": private, "public": public}


@pytest.fixture(scope="session")
def identity(agent_keys) -> IdentityMapper:
    mapper = IdentityMapper()
    mapper.register("agent://ml-platform", agent_keys["public"])
    mapper.bind("ml-service-account", "agent://ml-platform")
    return mapper


@pytest.fixture(scope="session")
def capabilities() -> CapabilityMapper:
    mapper = CapabilityMapper()
    mapper.grant_role("agent://ml-platform", "ml-engineer")
    return mapper


@pytest.fixture(scope="session")
def policies() -> PolicyEvaluator:
    return PolicyEvaluator(str(POLICY_DIR))


@pytest.fixture(scope="session")
def chain() -> ProvenanceChain:
    return ProvenanceChain(target="chain://morpheus/ml-platform")


@pytest.fixture(scope="session")
def client(endpoint, identity, capabilities, policies, chain, node_keys) -> GovernedClient:
    return GovernedClient(
        endpoint,
        identity,
        capabilities,
        policies,
        chain,
        node_keys["private"],
        node_keys["public"],
    )


@pytest.fixture()
def make_request(agent_keys):
    """Factory for signed, governed requests."""

    def _make(spec: dict, capability: str = "capability://compute/provision") -> GovernedRequest:
        request = GovernedRequest(
            action="provision-vm",
            agent_uri="agent://ml-platform",
            capability=capability,
            spec=spec,
            nonce=uuid.uuid4().hex,
            environment=spec.get("environment"),
        )
        request.signature = sign(canonical_json(request.message()), agent_keys["private"])
        return request

    return _make


@pytest.fixture(scope="session")
def quota() -> dict:
    return {"cpu_remaining": 16, "memory_gb_remaining": 64, "running_vms": 3}
