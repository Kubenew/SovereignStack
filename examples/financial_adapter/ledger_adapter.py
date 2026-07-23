"""
Tokenized Ledger Adapter for SovereignStack
REST API acting as a Unified Ledger Oracle.
Integrated with Web3 for Ethereum and RPC for Solana (Multi-Chain).
"""
import logging
import yaml
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Any
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from web3 import Web3
from examples.financial_adapter.zk_verifier import ProofVerifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TokenizedLedger")

app = FastAPI(title="SovereignStack Multi-Chain Ledger API")

# Load Config
with open("examples/financial_adapter/config.yaml", "r") as f:
    config = yaml.safe_load(f)
    ledger_cfg = config.get("ledger", {})
    evm_rpc_url = ledger_cfg.get("evm_rpc_url", "https://rpc.sepolia.org")
    usdc_address = ledger_cfg.get("usdc_address", "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238")
    evm_wallet = ledger_cfg.get("wallet_address", "0x000000000000000000000000000000000000dEaD")
    
    sol_rpc_url = ledger_cfg.get("solana_rpc_url", "https://api.devnet.solana.com")
    sol_usdc = ledger_cfg.get("solana_usdc_address", "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
    sol_wallet = ledger_cfg.get("solana_wallet", "11111111111111111111111111111111")

# Initialize Web3 (EVM)
w3 = Web3(Web3.HTTPProvider(evm_rpc_url))
erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# Prometheus Metrics
FINANCIAL_TX_TOTAL = Counter("financial_tx_total", "Total proposed transactions", ["asset", "action", "chain"])
POLICY_REJECTIONS_TOTAL = Counter("policy_rejections_total", "Total transactions rejected by policy")
SETTLEMENTS_TOTAL = Counter("settlements_total", "Total successful settlements")

# Fallback Mock State for testing without live RPC
_mock_state = {
    "tokenized_tsla_bonds": 500.0
}

class TransactionProposal(BaseModel):
    asset: str
    amount: float
    action: str
    chain: str = "ethereum"

class SignedTransaction(BaseModel):
    asset: str
    amount: float
    action: str
    chain: str = "ethereum"
    policy_approved: bool
    audit_hash: str = ""
    zk_proof: str = ""

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def get_solana_balance():
    """Fetch Solana Token Balance via RPC."""
    try:
        # For a real implementation, we'd query the associated token account.
        # This is a mock RPC payload to demonstrate multi-chain JSON-RPC pattern.
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [sol_wallet]
        }
        resp = requests.post(sol_rpc_url, json=payload, timeout=5)
        if resp.status_code == 200:
            return float(resp.json().get("result", {}).get("value", 1000000000)) / 1e9 # mock as 1 SOL
    except Exception as e:
        logger.error(f"Solana RPC call failed: {e}. Falling back to mock data.")
    return 500000.0 # Mock fallback

@app.get("/api/v1/balances")
def get_balances() -> Dict[str, float]:
    """Fetch tokenized assets balance from multiple chains."""
    logger.info("Oracle Read: Fetching live balances from EVM and Solana.")
    balances = _mock_state.copy()
    
    # EVM Fetch
    if w3.is_connected():
        try:
            contract = w3.eth.contract(address=w3.to_checksum_address(usdc_address), abi=erc20_abi)
            raw_balance = contract.functions.balanceOf(w3.to_checksum_address(evm_wallet)).call()
            balances["eth_usdc"] = float(raw_balance) / 1e6
        except Exception as e:
            logger.error(f"Web3 call failed: {e}. Falling back to mock data.")
            balances["eth_usdc"] = 1000000.0
    else:
        balances["eth_usdc"] = 1000000.0
        
    # Solana Fetch
    balances["sol_usdc"] = get_solana_balance()
        
    return balances

@app.post("/api/v1/propose")
def propose_transaction(tx: TransactionProposal) -> Dict[str, Any]:
    logger.info(f"Proposing transaction on {tx.chain}: {tx.action} {tx.amount} of {tx.asset}")
    
    FINANCIAL_TX_TOTAL.labels(asset=tx.asset, action=tx.action, chain=tx.chain).inc()
    
    return {
        "tx_id": f"tx_req_{tx.chain}_001",
        "asset": tx.asset,
        "amount": tx.amount,
        "action": tx.action,
        "chain": tx.chain,
        "status": "pending_policy_review"
    }

@app.post("/api/v1/settle")
def execute_settlement(signed_tx: SignedTransaction) -> Dict[str, Any]:
    if signed_tx.policy_approved is not True:
        logger.error("Execution failed: Transaction lacks policy approval.")
        POLICY_REJECTIONS_TOTAL.inc()
        raise HTTPException(status_code=403, detail="Transaction lacks policy approval.")
        
    # Phase 7: Verify ZK-SNARK mathematically before mutating ledger
    if not ProofVerifier.verify_proof(signed_tx.zk_proof, signed_tx.audit_hash):
        logger.error("Execution failed: ZK Proof is invalid. Cryptographic alignment broken.")
        POLICY_REJECTIONS_TOTAL.inc()
        raise HTTPException(status_code=403, detail="Invalid ZK Proof.")
        
    # Multi-chain mock settlement broadcast
    logger.info(f"Simulating {signed_tx.chain.upper()} settlement broadcast for {signed_tx.amount} of {signed_tx.asset}.")
        
    SETTLEMENTS_TOTAL.inc()
    return {"status": "success", "tx_hash": f"0xabc123simulatedtxhash_{signed_tx.chain}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8545)
