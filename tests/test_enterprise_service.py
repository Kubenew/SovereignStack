import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATA_DIR"] = "./data_test"

from services.enterprise_service import app

client = TestClient(app)


def clean_data():
    for f in ["contracts.json", "support_tickets.json", "update_history.json"]:
        p = os.path.join("data_test", f)
        if os.path.exists(p):
            os.remove(p)


@pytest.fixture(autouse=True)
def setup():
    clean_data()
    yield
    clean_data()


class TestEnterpriseHealth:
    def test_health_endpoint(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "enterprise"


class TestSupportContract:
    def test_no_contract_by_default(self):
        r = client.get("/enterprise/contract")
        assert r.status_code == 200
        data = r.json()
        assert data["active"] is False

    def test_create_contract(self):
        r = client.post("/enterprise/contract", json={
            "customer_name": "TestCorp",
            "tier": "enterprise",
            "max_nodes": 5,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "activated"
        assert data["contract"]["tier"] == "enterprise"
        assert data["contract"]["max_nodes"] == 5

    def test_get_contract_after_create(self):
        client.post("/enterprise/contract", json={
            "customer_name": "TestCorp",
            "tier": "enterprise",
        })
        r = client.get("/enterprise/contract")
        assert r.status_code == 200
        assert r.json()["active"] is True


class TestSLAMetrics:
    def test_sla_no_contract(self):
        r = client.get("/enterprise/sla")
        assert r.status_code == 200
        assert r.json()["status"] == "no_contract"

    def test_sla_with_contract(self):
        client.post("/enterprise/contract", json={"customer_name": "Acme"})
        r = client.get("/enterprise/sla")
        data = r.json()
        assert data["contract_tier"] == "standard"
        assert data["resolution_rate"] == 100.0


class TestSupportTickets:
    def test_create_ticket(self):
        r = client.post("/enterprise/ticket", json={
            "subject": "GPU failure",
            "description": "Node 3 GPU not responding",
            "severity": "high",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "created"
        assert data["ticket"]["severity"] == "high"

    def test_list_tickets(self):
        client.post("/enterprise/ticket", json={"subject": "Issue A"})
        client.post("/enterprise/ticket", json={"subject": "Issue B"})
        r = client.get("/enterprise/tickets")
        assert r.status_code == 200
        assert r.json()["count"] == 2

    def test_list_tickets_by_status(self):
        client.post("/enterprise/ticket", json={"subject": "Open issue"})
        r = client.get("/enterprise/tickets?status=open")
        assert r.json()["count"] == 1
        r = client.get("/enterprise/tickets?status=resolved")
        assert r.json()["count"] == 0

    def test_get_ticket_by_id(self):
        create = client.post("/enterprise/ticket", json={"subject": "Found me"}).json()
        tid = create["ticket"]["id"]
        r = client.get(f"/enterprise/tickets/{tid}")
        assert r.status_code == 200
        assert r.json()["ticket"]["subject"] == "Found me"

    def test_get_ticket_not_found(self):
        r = client.get("/enterprise/tickets/nonexistent")
        assert r.status_code == 404

    def test_resolve_ticket(self):
        create = client.post("/enterprise/ticket", json={"subject": "Fix me"}).json()
        tid = create["ticket"]["id"]
        r = client.post(f"/enterprise/tickets/{tid}/resolve")
        assert r.status_code == 200
        assert r.json()["ticket"]["status"] == "resolved"

    def test_ticket_gets_sla_deadline(self):
        client.post("/enterprise/contract", json={"customer_name": "Acme", "sla_response_hours": 4})
        r = client.post("/enterprise/ticket", json={"subject": "Urgent"})
        assert r.status_code == 200
        assert "sla_deadline" in r.json()["ticket"]


class TestManagedUpdates:
    def test_check_updates(self):
        r = client.get("/enterprise/updates/check")
        assert r.status_code == 200
        data = r.json()
        assert "current_version" in data
        assert "updates_available" in data

    def test_apply_update_needs_confirmation(self):
        r = client.post("/enterprise/updates/apply", json={"update_id": "v2026.4"})
        assert r.status_code == 200
        assert r.json()["status"] == "confirmation_required"

    def test_apply_update_with_confirmation(self):
        r = client.post("/enterprise/updates/apply", json={
            "update_id": "v2026.4",
            "confirm": True,
        })
        assert r.status_code == 200
        assert r.json()["status"] == "update_applied"

    def test_update_history(self):
        client.post("/enterprise/updates/apply", json={
            "update_id": "v2026.4", "confirm": True
        })
        r = client.get("/enterprise/updates/check")
        assert len(r.json()["update_history"]) == 1


class TestLicense:
    def test_no_license(self):
        r = client.get("/enterprise/license")
        assert r.json()["licensed"] is False

    def test_license_after_contract(self):
        client.post("/enterprise/contract", json={
            "customer_name": "Corp",
            "tier": "enterprise-plus",
            "features": ["audit", "sla"],
        })
        r = client.get("/enterprise/license")
        data = r.json()
        assert data["licensed"] is True
        assert data["tier"] == "enterprise-plus"
        assert "audit" in data["features"]
