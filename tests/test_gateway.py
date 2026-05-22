import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Set environment variables for testing before importing the app
os.environ["OASA_ENFORCE_COMPLIANCE"] = "STRICT"
os.environ["COMPUTE_URL"] = "http://mock-compute"
os.environ["MEMORY_URL"] = "http://mock-memory"
os.environ["DATA_DIR"] = "./data_test"

from services.gateway_service import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_data():
    # Clean up test audit logs
    if os.path.exists("./data_test/audit.log"):
        try:
            os.remove("./data_test/audit.log")
        except OSError:
            pass
    yield

def test_gateway_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gateway"}

def test_gateway_strict_missing_lock():
    # In STRICT mode, missing compliance lock should return 400 Bad Request
    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": False
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 400
    res_json = response.json()
    assert "error" in res_json
    assert res_json["error"]["code"] == "400"
    assert "lock is required" in res_json["error"]["message"]

@patch("requests.post")
def test_gateway_strict_with_lock_success(mock_post):
    # Mock compute endpoint to return success
    mock_compute_response = MagicMock()
    mock_compute_response.status_code = 200
    mock_compute_response.json.return_value = {"response": "This is a local response"}
    
    mock_memory_response = MagicMock()
    mock_memory_response.status_code = 200
    mock_memory_response.json.return_value = {"context": "Some context"}
    
    # We patch requests.post to return mock responses
    def side_effect(url, *args, **kwargs):
        if "compute" in url:
            return mock_compute_response
        elif "memory" in url:
            return mock_memory_response
        return MagicMock(status_code=404)
        
    mock_post.side_effect = side_effect

    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": True,
        "oasa_audit_tag": "TEST-123",
        "oasa_jurisdiction": "EU-GDPR"
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["choices"][0]["message"]["content"] == "This is a local response"
    assert res_json["model"] == "sovereign-llama3"

@patch("requests.post")
def test_gateway_strict_with_lock_failure(mock_post):
    # Mock compute endpoint to fail (return 500)
    mock_compute_response = MagicMock()
    mock_compute_response.status_code = 500
    
    mock_memory_response = MagicMock()
    mock_memory_response.status_code = 200
    mock_memory_response.json.return_value = {"context": ""}

    def side_effect(url, *args, **kwargs):
        if "compute" in url:
            return mock_compute_response
        elif "memory" in url:
            return mock_memory_response
        return MagicMock(status_code=404)

    mock_post.side_effect = side_effect

    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": True
    }
    # Should fail closed with 503 Service Unavailable
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 503
    res_json = response.json()
    assert "error" in res_json
    assert res_json["error"]["code"] == "503"
    assert "OASA-Lock prevented external fallback" in res_json["error"]["message"]

@patch("requests.post")
def test_gateway_non_strict_fallback(mock_post):
    # Run in DEVELOPMENT (non-strict) mode by patching the environment variable
    with patch.dict(os.environ, {"OASA_ENFORCE_COMPLIANCE": "DEVELOPMENT"}):
        mock_compute_response = MagicMock()
        mock_compute_response.status_code = 500  # local compute fails
        
        def side_effect(url, *args, **kwargs):
            if "compute" in url:
                return mock_compute_response
            return MagicMock(status_code=404)

        mock_post.side_effect = side_effect

        payload = {
            "model": "sovereign-llama3",
            "messages": [{"role": "user", "content": "Hello"}],
            "oasa_compliance_lock": False  # lock is False
        }
        # In non-strict mode, failing compute with lock=False should trigger simulated external fallback
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        res_json = response.json()
        assert "[FALLBACK - api.openai.com]" in res_json["choices"][0]["message"]["content"]
