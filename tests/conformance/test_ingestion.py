"""
Volatile Ingestion & Memory Processing Tests — OASA Conformance L1/L2
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

os.environ.setdefault("DATA_DIR", "./data_test")
os.environ.setdefault("OASA_ENFORCE_COMPLIANCE", "STRICT")

from services.ingest_service import app

client = TestClient(app)


def test_ingestion_endpoint_exists():
    """Ingestion service must expose health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("service") == "ingest", "Expected ingest service"


def test_ingestion_accepts_pdf_content():
    """Ingestion must accept file uploads."""
    response = client.post(
        "/ingest",
        files={"file": ("test.txt", b"Hello, this is a test document content", "text/plain")},
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "doc_id" in data, "Response must contain doc_id"
    assert "sha256" in data, "Response must contain sha256"


def test_ingestion_volatile_mode_config():
    """Verify sovereign-stack.yaml has volatile memory processing configured."""
    import yaml
    config_path = Path(__file__).resolve().parent.parent.parent / "sovereign-stack.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    ingest = config.get("data_ingestion", {})
    mode = ingest.get("memory_processing_mode", "")
    assert mode == "VOLATILE_RAM_ONLY", f"Expected VOLATILE_RAM_ONLY, got {mode}"


def test_ingestion_returns_sha256():
    """Ingested documents must return SHA-256 hash for integrity verification."""
    response = client.post(
        "/ingest",
        files={"file": ("report.pdf", b"Enterprise report content with PII", "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sha256"]) == 64, f"SHA-256 must be 64 hex chars, got {len(data['sha256'])}"
    assert data["sha256"].isalnum(), "SHA-256 must be alphanumeric"
