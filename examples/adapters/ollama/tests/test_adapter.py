"""Unit tests for the Ollama adapter."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_audit_log(tmp_path):
    log_path = tmp_path / "audit.log"
    log_path.touch()
    return str(log_path)


@pytest.fixture
def client(temp_audit_log):
    import adapter
    adapter._config["audit_log"] = temp_audit_log
    adapter._config["node_url"] = "http://localhost:9999"
    adapter._config["jurisdiction"] = "us"
    adapter._model_cache = {"llama3.1": {"uri": "model://ollama/llama3.1"}}
    return TestClient(adapter.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["adapter"] == "ollama"


def test_list_models(client):
    with patch("adapter._discover_models", new_callable=AsyncMock) as mock:
        mock.return_value = [{"name": "llama3.1", "size": 4000000000}]
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "ollama/llama3.1"
        assert "capabilities_uri" in data["data"][0]


def test_chat_completions_no_model(client):
    resp = client.post("/v1/chat/completions", json={"messages": []})
    assert resp.status_code == 400


def test_chat_completions_no_messages(client):
    resp = client.post("/v1/chat/completions", json={"model": "llama3.1"})
    assert resp.status_code == 400


def test_audit_log_written(client, temp_audit_log):
    import adapter
    adapter._write_audit({"type": "test", "data": "hello"})
    content = Path(temp_audit_log).read_text()
    entry = json.loads(content.strip())
    assert entry["type"] == "test"
    assert entry["data"] == "hello"


def test_hash_content():
    from adapter import _hash_content
    h = _hash_content("hello world")
    assert len(h) == 64
    assert h == _hash_content("hello world")
