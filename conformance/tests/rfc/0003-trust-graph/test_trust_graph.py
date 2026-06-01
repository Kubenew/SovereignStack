"""RFC-0003: Trust Graph — conformance tests for trust scores and web-of-trust."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_trust_score_onboard():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/trust/set",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"agent": "agent://newcomer", "score": 0.5})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "ok"


def test_trust_record_success():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/trust/record",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"agent": "agent://reliable", "outcome": "success", "latency_ms": 200})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0


def test_trust_record_failure():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/trust/record",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"agent": "agent://unreliable", "outcome": "failure"})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0


def test_trust_score_retrieval():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/trust/score", "-G", "--data-urlencode", "agent=agent://reliable"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    score = json.loads(result.stdout)
    assert 0.0 <= score["trust_score"] <= 1.0


def test_trust_web_attestation():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/trust/attest",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "subject": "agent://peer",
             "attester": "agent://trusted-vetter",
             "endorsement": 0.8
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0


def test_trust_graph_query():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/trust/graph", "-G",
         "--data-urlencode", "agent=agent://reliable",
         "--data-urlencode", "depth=2"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    graph = json.loads(result.stdout)
    assert "nodes" in graph
    assert "edges" in graph


def test_trust_threshold_filter():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/trust/filter", "-G",
         "--data-urlencode", "min_score=0.7"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    agents = json.loads(result.stdout)
    assert isinstance(agents, list)
