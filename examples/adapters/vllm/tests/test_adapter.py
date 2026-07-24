"""Unit tests for the vLLM adapter."""

import json
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
    adapter._model_cache = {"meta-llama/Llama-3.1-70B": {"uri": "model://vllm/meta-llama/Llama-3.1-70B"}}
    return TestClient(adapter.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["adapter"] == "vllm"


def test_list_models(client):
    with patch("adapter._discover_models", new_callable=AsyncMock) as mock:
        mock.return_value = [{"id": "meta-llama/Llama-3.1-70B", "owned_by": "meta"}]
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert "vllm/meta-llama" in data["data"][0]["id"]


def test_chat_no_model(client):
    resp = client.post("/v1/chat/completions", json={"messages": []})
    assert resp.status_code == 400


def test_chat_no_messages(client):
    resp = client.post("/v1/chat/completions", json={"model": "test"})
    assert resp.status_code == 400


def test_audit_written(client, temp_audit_log):
    import adapter
    adapter._write_audit({"type": "test", "data": "hello"})
    content = Path(temp_audit_log).read_text()
    entry = json.loads(content.strip())
    assert entry["type"] == "test"


def test_hash_content():
    from adapter import _hash_content
    h = _hash_content("test content")
    assert len(h) == 64
