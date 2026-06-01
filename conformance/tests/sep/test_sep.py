"""SEP conformance tests — Sovereign Extension Protocol."""
import json
import subprocess

SEP_ENDPOINT = "http://localhost:8547/sep/v1"


def test_sep_extension_registration():
    ext = {
        "name": "test-extension",
        "version": "1.0.0",
        "capabilities": ["custom:test"],
        "endpoint": "/ext/test"
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SEP_ENDPOINT}/register",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(ext)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "extension_id" in response
    assert response["status"] == "registered"


def test_sep_extension_discovery():
    result = subprocess.run(
        ["curl", "-s", f"{SEP_ENDPOINT}/extensions"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert isinstance(response, list)


def test_sep_extension_lifecycle():
    ext_id = "test-ext-001"
    result = subprocess.run(
        ["curl", "-s", f"{SEP_ENDPOINT}/extensions/{ext_id}/status"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "status" in response
    assert response["status"] in ("active", "inactive", "error")


def test_sep_extension_removal():
    ext_id = "test-ext-001"
    result = subprocess.run(
        ["curl", "-s", "-X", "DELETE", f"{SEP_ENDPOINT}/extensions/{ext_id}"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "removed"
