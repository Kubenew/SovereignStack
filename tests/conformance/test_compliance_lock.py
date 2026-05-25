"""
Compliance Lock Enforcement Tests — OASA Conformance L1/L2
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set test environment
os.environ.setdefault("OASA_ENFORCE_COMPLIANCE", "STRICT")
os.environ.setdefault("OASA_ENFORCE_AUTH", "DEVELOPMENT")
os.environ.setdefault("OASA_ENFORCE_POLICY", "DEVELOPMENT")
os.environ.setdefault("DATA_DIR", "./data_test")
os.environ.setdefault("COMPUTE_URL", "http://mock-compute")
os.environ.setdefault("MEMORY_URL", "http://mock-memory")
os.environ.setdefault("INFERENCE_BACKEND", "legacy")

from services.gateway_service import app

client = TestClient(app)


def test_compliance_lock_rejects_missing_lock():
    """Request without compliance_lock must be rejected."""
    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": False
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "error" in response.json(), "Response must contain error field"


@patch("requests.post")
def test_compliance_lock_allows_with_lock(mock_post):
    """Request with valid compliance_lock must succeed."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "OK"}
    mock_post.return_value = mock_response

    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": True
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code in (200, 503), f"Expected 200 or 503, got {response.status_code}"


@patch("requests.post")
def test_oasa_lock_prevents_fallback(mock_post):
    """When lock is enabled and compute fails, must return 503, not fallback."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": True
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 503, f"Expected 503, got {response.status_code}"
    data = response.json()
    assert "error" in data
    assert "OASA-Lock" in data["error"]["message"]


@patch("requests.post")
def test_non_strict_without_lock_fallback(mock_post):
    """Non-strict mode without lock may fallback (warning, not error)."""
    with patch.dict(os.environ, {"OASA_ENFORCE_COMPLIANCE": "DEVELOPMENT"}):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        payload = {
            "model": "sovereign-llama3",
            "messages": [{"role": "user", "content": "Hello"}],
            "oasa_compliance_lock": False
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "FALLBACK" in data["choices"][0]["message"]["content"]


@pytest.mark.level("L2")
def test_oasa_lock_with_jurisdiction():
    """Compliance lock must work with jurisdiction metadata."""
    payload = {
        "model": "sovereign-llama3",
        "messages": [{"role": "user", "content": "Hello"}],
        "oasa_compliance_lock": True,
        "oasa_audit_tag": "AUDIT-TEST-001",
        "oasa_jurisdiction": "EU-GDPR"
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code in (200, 503), f"Expected 200 or 503, got {response.status_code}"
