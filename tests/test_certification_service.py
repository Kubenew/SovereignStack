import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATA_DIR"] = "./data_test"

from services.certification_service import app

client = TestClient(app)


def clean_registry():
    p = os.path.join("data_test", "certification_registry.json")
    if os.path.exists(p):
        os.remove(p)


@pytest.fixture(autouse=True)
def setup():
    clean_registry()
    yield
    clean_registry()


class TestCertificationHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "certification"


class TestCertificationPrograms:
    def test_list_programs(self):
        r = client.get("/certification/programs")
        assert r.status_code == 200
        data = r.json()
        assert "node" in data["programs"]
        assert "runtime" in data["programs"]
        assert "federation" in data["programs"]

    def test_get_program_node(self):
        r = client.get("/certification/programs/node")
        assert r.status_code == 200
        assert r.json()["program"] == "node"

    def test_get_program_not_found(self):
        r = client.get("/certification/programs/invalid")
        assert r.status_code == 404


class TestCertificationRegistry:
    def test_register_node(self):
        r = client.post("/certification/registry", json={
            "subject_name": "My Sovereign Node",
            "program": "node",
            "level": "L2",
            "contact": "admin@example.com",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "registered"
        assert data["entry"]["program"] == "node"
        assert data["entry"]["level"] == "L2"
        assert data["entry"]["status"] == "active"

    def test_register_runtime(self):
        r = client.post("/certification/registry", json={
            "subject_name": "OASA Gateway v2",
            "program": "runtime",
            "level": "L3",
        })
        assert r.status_code == 200
        assert r.json()["entry"]["program"] == "runtime"

    def test_register_federation(self):
        r = client.post("/certification/registry", json={
            "subject_name": "Mesh Relay Alpha",
            "program": "federation",
            "level": "L1",
        })
        assert r.status_code == 200
        assert r.json()["entry"]["program"] == "federation"

    def test_register_invalid_program(self):
        r = client.post("/certification/registry", json={
            "subject_name": "Bad",
            "program": "unknown",
            "level": "L1",
        })
        assert r.status_code == 400

    def test_register_invalid_level(self):
        r = client.post("/certification/registry", json={
            "subject_name": "Bad",
            "program": "node",
            "level": "L4",
        })
        assert r.status_code == 400

    def test_list_registry(self):
        client.post("/certification/registry", json={
            "subject_name": "Node A", "program": "node", "level": "L2"
        })
        client.post("/certification/registry", json={
            "subject_name": "Runtime B", "program": "runtime", "level": "L1"
        })
        r = client.get("/certification/registry")
        assert r.status_code == 200
        assert r.json()["count"] == 2

    def test_list_registry_filter_program(self):
        client.post("/certification/registry", json={
            "subject_name": "Node A", "program": "node", "level": "L2"
        })
        client.post("/certification/registry", json={
            "subject_name": "Runtime B", "program": "runtime", "level": "L1"
        })
        r = client.get("/certification/registry?program=node")
        assert r.json()["count"] == 1
        assert r.json()["entries"][0]["program"] == "node"

    def test_list_registry_filter_level(self):
        client.post("/certification/registry", json={
            "subject_name": "Node A", "program": "node", "level": "L2"
        })
        client.post("/certification/registry", json={
            "subject_name": "Node B", "program": "node", "level": "L1"
        })
        r = client.get("/certification/registry?level=L2")
        assert r.json()["count"] == 1

    def test_list_registry_filter_status(self):
        client.post("/certification/registry", json={
            "subject_name": "Node A", "program": "node", "level": "L2"
        })
        r = client.get("/certification/registry?status=active")
        assert r.json()["count"] == 1
        r = client.get("/certification/registry?status=revoked")
        assert r.json()["count"] == 0

    def test_get_entry_by_id(self):
        create = client.post("/certification/registry", json={
            "subject_name": "Find Me", "program": "node", "level": "L1"
        }).json()
        eid = create["entry"]["id"]
        r = client.get(f"/certification/registry/{eid}")
        assert r.status_code == 200
        assert r.json()["subject_name"] == "Find Me"

    def test_get_entry_not_found(self):
        r = client.get("/certification/registry/nonexistent")
        assert r.status_code == 404

    def test_update_entry_status(self):
        create = client.post("/certification/registry", json={
            "subject_name": "Revocable", "program": "node", "level": "L1"
        }).json()
        eid = create["entry"]["id"]
        r = client.post(f"/certification/registry/{eid}/status", json={"status": "revoked"})
        assert r.status_code == 200
        assert r.json()["entry"]["status"] == "revoked"

    def test_update_entry_invalid_status(self):
        create = client.post("/certification/registry", json={
            "subject_name": "Bad", "program": "node", "level": "L1"
        }).json()
        eid = create["entry"]["id"]
        r = client.post(f"/certification/registry/{eid}/status", json={"status": "bogus"})
        assert r.status_code == 400


class TestCertificationVerify:
    def test_verify_valid_entry(self):
        create = client.post("/certification/registry", json={
            "subject_name": "Valid Node", "program": "node", "level": "L2"
        }).json()
        eid = create["entry"]["id"]
        r = client.get(f"/certification/verify/{eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is True
        assert data["status"] == "active"
        assert data["expired"] is False

    def test_verify_revoked_entry(self):
        create = client.post("/certification/registry", json={
            "subject_name": "Revoked Node", "program": "node", "level": "L1"
        }).json()
        eid = create["entry"]["id"]
        client.post(f"/certification/registry/{eid}/status", json={"status": "revoked"})
        r = client.get(f"/certification/verify/{eid}")
        assert r.json()["valid"] is False

    def test_verify_not_found(self):
        r = client.get("/certification/verify/nonexistent")
        assert r.status_code == 404
