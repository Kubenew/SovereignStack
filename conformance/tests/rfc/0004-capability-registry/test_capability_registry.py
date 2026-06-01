"""RFC-0004: Capability Registry — conformance tests for ACP discovery."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_capability_register():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/capabilities/register",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "provider": "agent://agent-1",
             "capability": "contract_review",
             "accuracy": 0.94,
             "cost": 0.02,
             "latency_ms": 3000,
             "languages": ["en", "cs"],
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "registered"


def test_capability_query():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/capabilities/query", "-G",
         "--data-urlencode", "capability=contract_review"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    results = json.loads(result.stdout)
    assert isinstance(results, list)


def test_capability_query_with_filters():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/capabilities/query", "-G",
         "--data-urlencode", "capability=contract_review",
         "--data-urlencode", "min_accuracy=0.9",
         "--data-urlencode", "language=en"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    results = json.loads(result.stdout)
    for r in results:
        assert r["score"] >= 0.0


def test_capability_binding():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/capabilities/bind",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "capability": "contract_review",
             "consumer": "agent://consumer-1",
             "provider": "agent://agent-1",
             "max_calls": 10,
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    binding = json.loads(result.stdout)
    assert binding["status"] == "Active"


def test_capability_revoke():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/capabilities/revoke",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"provider": "agent://bad-actor"})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "revoked"


def test_capability_list():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/capabilities/list"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    caps = json.loads(result.stdout)
    assert isinstance(caps, list)
