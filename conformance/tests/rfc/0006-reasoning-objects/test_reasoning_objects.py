"""RFC-0006: Reasoning Objects — conformance tests for reasoning chains."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_reasoning_chain_create():
    chain = {
        "id": "reasoning://org/analysis/v1",
        "goal": "Determine optimal contract terms",
        "steps": [
            {"order": 1, "type": "premise", "content": "Party A requires escrow", "confidence": 0.9},
            {"order": 2, "type": "inference", "content": "Escrow requires third-party", "confidence": 0.85},
            {"order": 3, "type": "conclusion", "content": "Appoint TrustedAgent as escrow", "confidence": 0.8},
        ],
        "source": "agent://legal-analyst",
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/reasoning/chains",
         "-H", "Content-Type: application/json", "-d", json.dumps(chain)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "stored"


def test_reasoning_step_validation():
    invalid = {
        "id": "reasoning://org/bad/v1",
        "goal": "Test",
        "steps": [
            {"order": 1, "type": "unknown_type", "content": "Invalid", "confidence": 0.5},
        ],
        "source": "agent://tester",
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/reasoning/chains",
         "-H", "Content-Type: application/json", "-d", json.dumps(invalid)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "error" in response


def test_reasoning_chain_retrieval():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/reasoning/chains", "-G",
         "--data-urlencode", "id=reasoning://org/analysis/v1"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    chain = json.loads(result.stdout)
    assert "steps" in chain


def test_reasoning_explain():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/reasoning/explain", "-G",
         "--data-urlencode", "id=reasoning://org/analysis/v1"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    explanation = json.loads(result.stdout)
    assert "explanation" in explanation or "steps" in explanation


def test_reasoning_confidence_aggregate():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/reasoning/confidence", "-G",
         "--data-urlencode", "id=reasoning://org/analysis/v1"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    conf = json.loads(result.stdout)
    assert 0.0 <= conf.get("aggregate_confidence", 0.0) <= 1.0


def test_reasoning_search_by_goal():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/reasoning/search", "-G",
         "--data-urlencode", "q=contract terms"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    results = json.loads(result.stdout)
    assert isinstance(results, list)
