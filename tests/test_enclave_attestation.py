import pytest
import base64
from fastapi.testclient import TestClient
from services.enclave_attestation import app, _attestation_cache, ATTESTATION_TTL

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_cache():
    _attestation_cache.clear()
    yield

class TestEnclaveAttestation:
    
    def test_attest_sgx_valid(self):
        req = {
            "node_id": "test-node",
            "enclave_type": "sgx",
            "quote_b64": base64.b64encode(b"fake-quote").decode(),
            "public_key_b64": base64.b64encode(b"fake-pubkey").decode(),
            "nonce": "12345"
        }
        resp = client.post("/attest", json=req)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "verified"
        assert data["node_id"] == "test-node"
        assert "attestation_token" in data
        
        # Verify cache
        assert "test-node" in _attestation_cache

    def test_attest_sev_snp_valid(self):
        req = {
            "node_id": "test-node-2",
            "enclave_type": "sev-snp",
            "quote_b64": base64.b64encode(b"fake-report").decode(),
            "public_key_b64": base64.b64encode(b"fake-pubkey").decode(),
            "nonce": "12345"
        }
        resp = client.post("/attest", json=req)
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"

    def test_attest_invalid_base64(self):
        req = {
            "node_id": "test-node",
            "enclave_type": "sgx",
            "quote_b64": "not-base64-!@#",
            "public_key_b64": "fake",
            "nonce": "123"
        }
        resp = client.post("/attest", json=req)
        assert resp.status_code == 400

    def test_attest_unsupported_type(self):
        req = {
            "node_id": "test-node",
            "enclave_type": "aws-nitro",
            "quote_b64": base64.b64encode(b"fake").decode(),
            "public_key_b64": base64.b64encode(b"fake").decode(),
            "nonce": "123"
        }
        resp = client.post("/attest", json=req)
        assert resp.status_code == 400

    def test_check_status_found(self):
        req = {
            "node_id": "status-node",
            "enclave_type": "sgx",
            "quote_b64": base64.b64encode(b"fake").decode(),
            "public_key_b64": base64.b64encode(b"fake").decode(),
            "nonce": "123"
        }
        client.post("/attest", json=req)
        
        resp = client.get("/attest/status/status-node")
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_id"] == "status-node"
        assert data["enclave_type"] == "sgx"

    def test_check_status_not_found(self):
        resp = client.get("/attest/status/unknown-node")
        assert resp.status_code == 404

    def test_check_status_expired(self, monkeypatch):
        # Create a fake entry that is already expired
        import time
        from services.enclave_attestation import AttestationCacheEntry
        
        now = time.time()
        _attestation_cache["expired-node"] = AttestationCacheEntry(
            node_id="expired-node",
            enclave_type="sgx",
            public_key_b64="fake",
            verified_at=now - 1000,
            expires_at=now - 500  # expired
        )
        
        resp = client.get("/attest/status/expired-node")
        assert resp.status_code == 404
        assert "expired-node" not in _attestation_cache # should be cleaned up
