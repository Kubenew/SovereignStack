"""RFC-0008: Federation Routing — conformance tests for cross-sovereign routing."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_federation_announce():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/federation/announce",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "node": "node://sovereign-1",
             "jurisdiction": "EU",
             "capabilities": ["knowledge_storage", "contract_review"],
             "latency_ms": 50,
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "announced"


def test_federation_discover():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/federation/discover", "-G",
         "--data-urlencode", "jurisdiction=EU",
         "--data-urlencode", "capability=knowledge_storage"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    nodes = json.loads(result.stdout)
    assert isinstance(nodes, list)


def test_federation_route():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/federation/route", "-G",
         "--data-urlencode", "source=node://sovereign-1",
         "--data-urlencode", "target=agent://remote-agent",
         "--data-urlencode", "jurisdiction=US"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    route = json.loads(result.stdout)
    assert "hops" in route or "path" in route


def test_federation_policy():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/federation/policy",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "node": "node://sovereign-1",
             "policy": {"allow_jurisdictions": ["EU", "US"], "min_trust": 0.5},
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "policy_set"


def test_federation_health():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/federation/health", "-G",
         "--data-urlencode", "node=node://sovereign-1"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    health = json.loads(result.stdout)
    assert "latency_ms" in health or "status" in health


def test_federation_topology():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/federation/topology"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    topo = json.loads(result.stdout)
    assert "nodes" in topo or isinstance(topo, list)
