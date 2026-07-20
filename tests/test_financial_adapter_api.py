import pytest
from fastapi.testclient import TestClient
from examples.financial_adapter.ledger_adapter import app

client = TestClient(app)

def test_get_balances():
    response = client.get("/api/v1/balances")
    assert response.status_code == 200
    assert response.json() == {
        "tokenized_usdc": 1000000.0,
        "tokenized_tsla_bonds": 500.0
    }

def test_propose_transaction():
    response = client.post("/api/v1/propose", json={
        "asset": "tokenized_tsla_bonds",
        "amount": 50.0,
        "action": "BUY"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "pending_policy_review"

def test_settle_transaction_approved():
    response = client.post("/api/v1/settle", json={
        "asset": "tokenized_tsla_bonds",
        "amount": 50.0,
        "action": "BUY",
        "policy_approved": True,
        "audit_hash": "0xABC"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_settle_transaction_unapproved():
    response = client.post("/api/v1/settle", json={
        "asset": "tokenized_tsla_bonds",
        "amount": 50.0,
        "action": "BUY",
        "policy_approved": False,
        "audit_hash": ""
    })
    assert response.status_code == 403

def test_prometheus_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "financial_tx_total_total" in response.text or "financial_tx_total" in response.text
