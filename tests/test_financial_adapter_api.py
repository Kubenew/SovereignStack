import pytest
from fastapi.testclient import TestClient
from examples.financial_adapter.ledger_adapter import app
from examples.financial_adapter.zk_verifier import ProofVerifier

client = TestClient(app)

def test_get_balances():
    response = client.get("/api/v1/balances")
    assert response.status_code == 200
    balances = response.json()
    assert "eth_usdc" in balances
    assert "sol_usdc" in balances

def test_propose_transaction_solana():
    response = client.post("/api/v1/propose", json={
        "asset": "sol_usdc",
        "amount": 10.0,
        "action": "SELL",
        "chain": "solana"
    })
    assert response.status_code == 200
    assert response.json()["chain"] == "solana"

def test_settle_transaction_approved_with_zk():
    # Phase 7 & 8 integration test
    audit_hash = "0xABCD1234"
    valid_proof = ProofVerifier.generate_simulated_proof(audit_hash)
    
    response = client.post("/api/v1/settle", json={
        "asset": "tokenized_tsla_bonds",
        "amount": 50.0,
        "action": "BUY",
        "chain": "ethereum",
        "policy_approved": True,
        "audit_hash": audit_hash,
        "zk_proof": valid_proof
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_settle_transaction_approved_missing_zk():
    # Attempting to settle without a valid ZK proof
    response = client.post("/api/v1/settle", json={
        "asset": "tokenized_tsla_bonds",
        "amount": 50.0,
        "action": "BUY",
        "chain": "ethereum",
        "policy_approved": True,
        "audit_hash": "0xABCD",
        "zk_proof": "fake_proof_or_missing"
    })
    assert response.status_code == 403
    assert "Invalid ZK Proof" in response.json()["detail"]

def test_settle_transaction_unapproved():
    response = client.post("/api/v1/settle", json={
        "asset": "tokenized_tsla_bonds",
        "amount": 50.0,
        "action": "BUY",
        "chain": "solana",
        "policy_approved": False,
        "audit_hash": "",
        "zk_proof": ""
    })
    assert response.status_code == 403

def test_prometheus_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "financial_tx_total" in response.text
