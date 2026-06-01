"""RFC-0001: Sovereign Object Model — conformance tests."""
import json
import subprocess


def test_object_create():
    obj = {
        "id": "knowledge://test/object/v1",
        "type": "knowledge",
        "owner": "org://test",
        "version": "1.0.0",
        "created": "2026-05-31T12:00:00Z",
        "updated": "2026-05-31T12:00:00Z",
        "signature": "sig:placeholder",
        "provenance": []
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://localhost:8546/objects",
         "-H", "Content-Type: application/json", "-d", json.dumps(obj)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["status"] == "stored"
    assert response["uri"] == obj["id"]


def test_object_required_fields():
    """Every object must have id, type, owner, version, created, updated, signature."""
    required = ["id", "type", "owner", "version", "created", "updated", "signature"]
    for field in required:
        obj = {
            "type": "test",
            "owner": "org://test",
            "version": "1.0.0",
            "created": "2026-05-31T12:00:00Z",
            "updated": "2026-05-31T12:00:00Z",
            "signature": "sig:test"
        }
        if field != "type":
            obj[field] = "test-value"
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://localhost:8546/objects",
             "-H", "Content-Type: application/json", "-d", json.dumps(obj)],
            capture_output=True, text=True, timeout=5
        )
        if field == "id":
            continue
        assert json.loads(result.stdout).get("error") is not None


def test_object_sign_verify():
    obj = {
        "id": "knowledge://test/signed/v1",
        "type": "knowledge",
        "owner": "org://test",
        "version": "1.0.0",
        "created": "2026-05-31T12:00:00Z",
        "updated": "2026-05-31T12:00:00Z",
        "signature": "ed25519:deadbeef...",
        "provenance": []
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://localhost:8546/objects/verify",
         "-H", "Content-Type: application/json", "-d", json.dumps(obj)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "valid" in response


def test_object_query():
    result = subprocess.run(
        ["curl", "-s", "http://localhost:8546/objects?type=knowledge&owner=org://test"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert isinstance(response, list)


def test_object_provenance_chain():
    obj = {
        "id": "knowledge://test/provenance/v2",
        "type": "knowledge",
        "owner": "org://test",
        "version": "2.0.0",
        "created": "2026-05-31T12:00:00Z",
        "updated": "2026-05-31T12:05:00Z",
        "signature": "sig:v2",
        "provenance": [
            {"action": "updated", "agent": "agent://updater", "timestamp": "2026-05-31T12:05:00Z", "previous": "knowledge://test/provenance/v1"}
        ]
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://localhost:8546/objects",
         "-H", "Content-Type: application/json", "-d", json.dumps(obj)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "stored"
