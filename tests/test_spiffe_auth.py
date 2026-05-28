"""Tests for SPIFFE authentication module and inter-service auth."""

import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends

os.environ.setdefault("SPIFFE_ENABLED", "false")


class TestSpiffeAuth:
    def test_spiffe_disabled_returns_none(self):
        from services.spiffe_auth import require_spiffe_or_skip, spiffe_enabled

        assert spiffe_enabled() is False, "SPIFFE should be disabled in test"

    def test_spiffe_auth_skip_when_disabled(self):
        """When SPIFFE is disabled, require_spiffe_or_skip should return None."""
        from services.spiffe_auth import require_spiffe_or_skip

        import asyncio

        # It's an async dependency - verify it can handle no credentials
        async def _test():
            result = await require_spiffe_or_skip(credentials=None)
            assert result is None

        asyncio.run(_test())

    def test_authorized_spiffe_ids_disabled(self):
        """authorized_spiffe_ids should allow requests when SPIFFE disabled."""
        from services.spiffe_auth import authorized_spiffe_ids
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/test")
        def test_endpoint(identity: dict = Depends(authorized_spiffe_ids())):
            return identity

        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"spiffe_id": "unknown", "claims": {}}

    def test_spiffe_enabled_env(self):
        """SPIFFE_ENABLED=true should be detected."""
        with patch.dict(os.environ, {"SPIFFE_ENABLED": "true"}, clear=False):
            # Re-import requires module reload
            import importlib
            from services import spiffe_auth

            importlib.reload(spiffe_auth)
            assert spiffe_auth.spiffe_enabled() is True

    def test_spiffe_jwt_validation_rejects_malformed(self):
        """When SPIFFE enabled, malformed JWT should return 403."""
        with patch.dict(os.environ, {"SPIFFE_ENABLED": "true"}, clear=False):
            import importlib
            from services import spiffe_auth

            importlib.reload(spiffe_auth)

            app = FastAPI()

            @app.get("/test-auth")
            def test_endpoint(identity: dict = Depends(spiffe_auth.authorized_spiffe_ids())):
                return {"identity": identity}

            client = TestClient(app)
            response = client.get("/test-auth", headers={"Authorization": "Bearer invalid-token"})
            assert response.status_code == 403
            assert "SPIFFE JWT validation failed" in response.json()["detail"]

    def test_spiffe_jwt_no_auth_header(self):
        """When SPIFFE enabled but no auth header, should return 401."""
        with patch.dict(os.environ, {"SPIFFE_ENABLED": "true"}, clear=False):
            import importlib
            from services import spiffe_auth

            importlib.reload(spiffe_auth)

            app = FastAPI()

            @app.get("/test-auth")
            def test_endpoint(identity: dict = Depends(spiffe_auth.authorized_spiffe_ids())):
                return {"identity": identity}

            client = TestClient(app)
            response = client.get("/test-auth")
            assert response.status_code == 401
            assert "Missing SPIFFE JWT SVID" in response.json()["detail"]


class TestMemoryServiceAuth:
    def test_memory_health_with_spiffe(self):
        """Memory health endpoint works when SPIFFE disabled."""
        from services.memory_service import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "memory"
        assert data["spiffe_enabled"] is False

    def test_memory_embed_without_auth(self):
        """Memory embed works without auth when SPIFFE disabled."""
        from services.memory_service import app

        client = TestClient(app)
        response = client.post(
            "/embed",
            json={"doc_id": "test-doc", "text": "Hello world", "org_id": "default"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "stored"

    def test_memory_query_without_auth(self):
        """Memory query works without auth when SPIFFE disabled."""
        from services.memory_service import app

        client = TestClient(app)
        response = client.post("/query", json={"query": "Hello", "org_id": "default"})
        assert response.status_code == 200
        assert "matches" in response.json()


class TestIngestServiceAuth:
    def test_ingest_health_with_spiffe(self):
        """Ingest health endpoint works when SPIFFE disabled."""
        from services.ingest_service import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ingest"
        assert data["spiffe_enabled"] is False

    def test_ingest_upload_without_auth(self):
        """Ingest upload works without auth when SPIFFE disabled."""
        from services.ingest_service import app

        client = TestClient(app)
        response = client.post(
            "/ingest",
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert response.status_code == 200
        assert "doc_id" in response.json()
