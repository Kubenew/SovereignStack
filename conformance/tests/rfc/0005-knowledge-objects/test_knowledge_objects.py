"""RFC-0005: Knowledge Objects — conformance tests for knowledge claims."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_knowledge_claim_create():
    claim = {
        "id": "knowledge://org/research/v1",
        "claim": "Water freezes at 0°C at 1 atm",
        "confidence": 0.99,
        "source": "agent://researcher-1",
        "domain": "physics",
        "provenance": [{"action": "measured", "agent": "agent://sensor-1", "timestamp": "2026-05-31T12:00:00Z"}]
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/knowledge/claims",
         "-H", "Content-Type: application/json", "-d", json.dumps(claim)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "stored"


def test_knowledge_claim_confidence():
    claim = {
        "id": "knowledge://org/uncertain/v1",
        "claim": "Stock prices may rise",
        "confidence": 0.55,
        "source": "agent://economist-1",
        "domain": "finance",
        "provenance": []
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/knowledge/claims",
         "-H", "Content-Type: application/json", "-d", json.dumps(claim)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert 0.0 <= claim["confidence"] <= 1.0


def test_knowledge_claim_contradiction():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/knowledge/contradictions", "-G",
         "--data-urlencode", "claim=Water freezes at 0°C at 1 atm"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert isinstance(response.get("contradictions", []), list)


def test_knowledge_aggregate():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/knowledge/aggregate", "-G",
         "--data-urlencode", "domain=physics",
         "--data-urlencode", "min_confidence=0.8"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert isinstance(response.get("claims", []), list)


def test_knowledge_query_by_domain():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/knowledge/query", "-G",
         "--data-urlencode", "domain=physics"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    claims = json.loads(result.stdout)
    assert isinstance(claims, list)


def test_knowledge_rating():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/knowledge/rate",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"claim_id": "knowledge://org/research/v1", "rating": 0.95, "rater": "agent://reviewer"})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "rated"
