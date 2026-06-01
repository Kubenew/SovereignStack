"""SMP conformance tests — Sovereign Memory Protocol."""
import json
import subprocess

SMP_ENDPOINT = "http://localhost:8549/smp/v1"


def test_smp_memory_store():
    obj = {
        "key": "test:memory:001",
        "value": {"data": "hello world"},
        "ttl_seconds": 60
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "PUT", f"{SMP_ENDPOINT}/memory",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(obj)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["status"] == "stored"
    assert "uri" in response
    assert response["uri"].startswith("memory://")


def test_smp_memory_retrieve():
    uri = "memory://test:memory:001"
    result = subprocess.run(
        ["curl", "-s", f"{SMP_ENDPOINT}/memory/{uri}"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "value" in response
    assert "metadata" in response


def test_smp_memory_search():
    query = {"pattern": "test:*", "limit": 10}
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SMP_ENDPOINT}/memory/search",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(query)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert isinstance(response, list)


def test_smp_memory_delete():
    uri = "memory://test:memory:001"
    result = subprocess.run(
        ["curl", "-s", "-X", "DELETE", f"{SMP_ENDPOINT}/memory/{uri}"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "deleted"


def test_smp_memory_ttl():
    obj = {
        "key": "test:ttl:001",
        "value": {"data": "ephemeral"},
        "ttl_seconds": 1
    }
    subprocess.run(
        ["curl", "-s", "-X", "PUT", f"{SMP_ENDPOINT}/memory",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(obj)],
        capture_output=True, text=True, timeout=5
    )
    import time
    time.sleep(2)
    result = subprocess.run(
        ["curl", "-s", "-f", f"{SMP_ENDPOINT}/memory/memory://test:ttl:001"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode != 0
