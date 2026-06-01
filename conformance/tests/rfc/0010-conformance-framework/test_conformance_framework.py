"""RFC-0010: Conformance Framework — meta-conformance tests for the test suite."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_conformance_level_check():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/conformance/level"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    level = json.loads(result.stdout)
    assert level["level"] in ["L1", "L2", "L3"]


def test_conformance_profile_list():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/conformance/profiles"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    profiles = json.loads(result.stdout)
    assert isinstance(profiles, list)
    required = ["core-node", "federation-node", "knowledge-node", "agent-node"]
    for r in required:
        assert r in profiles


def test_conformance_run_all():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/conformance/run",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"profile": "core-node"})],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert "passed" in report
    assert "failed" in report
    assert "total" in report


def test_conformance_certification():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/conformance/certify",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "node_id": "node://test-node",
             "profile": "core-node",
         })],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    cert = json.loads(result.stdout)
    assert "certificate" in cert or "status" in cert


def test_conformance_rfc_coverage():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/conformance/coverage"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    coverage = json.loads(result.stdout)
    assert len(coverage["rfcs"]) == 10
    for rfc in coverage["rfcs"]:
        assert "0001" <= rfc["id"] <= "0010"
        assert rfc["has_tests"] is True


def test_conformance_l1_required():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/conformance/requirements/L1"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    reqs = json.loads(result.stdout)
    assert len(reqs) > 0
