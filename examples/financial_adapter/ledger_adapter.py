"""
Tokenized Ledger Adapter for SovereignStack
REST API acting as a Unified Ledger Oracle.
Now with Prometheus observability.
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Any
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TokenizedLedger")

app = FastAPI(title="SovereignStack Mock Ledger API")

# Prometheus Metrics
FINANCIAL_TX_TOTAL = Counter("financial_tx_total", "Total proposed transactions", ["asset", "action"])
POLICY_REJECTIONS_TOTAL = Counter("policy_rejections_total", "Total transactions rejected by policy")
SETTLEMENTS_TOTAL = Counter("settlements_total", "Total successful settlements")

# Mock State
_mock_state = {
    "tokenized_usdc": 1000000.0,
    "tokenized_tsla_bonds": 500.0
}

class TransactionProposal(BaseModel):
    asset: str
    amount: float
    action: str

class SignedTransaction(BaseModel):
    asset: str
    amount: float
    action: str
    policy_approved: bool
    audit_hash: str = ""

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/v1/balances")
def get_balances() -> Dict[str, float]:
    """Fetch tokenized assets balance."""
    logger.info("Oracle Read: Fetching balances from unified ledger.")
    return _mock_state.copy()

@app.post("/api/v1/propose")
def propose_transaction(tx: TransactionProposal) -> Dict[str, Any]:
    """
    Propose a transaction for policy review.
    """
    logger.info(f"Proposing transaction: {tx.action} {tx.amount} of {tx.asset}")
    
    if tx.asset not in _mock_state:
        raise HTTPException(status_code=400, detail="Asset not supported.")
        
    FINANCIAL_TX_TOTAL.labels(asset=tx.asset, action=tx.action).inc()
    
    return {
        "tx_id": "tx_req_001",
        "asset": tx.asset,
        "amount": tx.amount,
        "action": tx.action,
        "status": "pending_policy_review"
    }

@app.post("/api/v1/settle")
def execute_settlement(signed_tx: SignedTransaction) -> Dict[str, Any]:
    """
    Executes a transaction that has been signed and approved by SovereignStack Policy Engine.
    """
    if signed_tx.policy_approved is not True:
        logger.error("Execution failed: Transaction lacks policy approval.")
        POLICY_REJECTIONS_TOTAL.inc()
        raise HTTPException(status_code=403, detail="Transaction lacks policy approval.")
        
    asset = signed_tx.asset
    amount = signed_tx.amount
    
    if signed_tx.action == "BUY":
        _mock_state["tokenized_usdc"] -= (amount * 100) # Mock price
        _mock_state[asset] = _mock_state.get(asset, 0) + amount
    elif signed_tx.action == "SELL":
        _mock_state[asset] -= amount
        _mock_state["tokenized_usdc"] += (amount * 100)
        
    SETTLEMENTS_TOTAL.inc()
    logger.info(f"Settlement successful. New balances: {_mock_state}")
    return {"status": "success", "new_balances": _mock_state.copy()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8545)
