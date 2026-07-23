"""
Autonomous Agentic Swarm for the Sovereign Mesh.
Orchestrates Risk, Compliance, and Execution agents to debate and settle cross-chain trades.
"""
import logging
import requests
import json
import os
import time
import hashlib
from examples.financial_adapter.zk_verifier import ProofVerifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SwarmOrchestrator")

LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8545")
AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:9091")

class CRDTBulletinBoard:
    """Simulates a shared CRDT state where swarm agents communicate."""
    def __init__(self):
        self.state = {}

    def post(self, key: str, data: dict):
        self.state[key] = data

    def read(self, key: str) -> dict:
        return self.state.get(key, None)

class RiskAgent:
    """Analyzes markets and proposes trades."""
    def evaluate_markets(self, board: CRDTBulletinBoard):
        try:
            resp = requests.get(f"{LEDGER_URL}/api/v1/balances")
            balances = resp.json()
            logger.info(f"[RiskAgent] Perceived state: {balances}")
        except Exception as e:
            logger.error(f"[RiskAgent] Failed to read ledger: {e}")
            return
            
        # Example logic: Hedge EVM risk on Solana
        if balances.get("eth_usdc", 0) > 500000:
            logger.info("[RiskAgent] Arbitrage/Hedge opportunity detected. Proposing Solana swap.")
            proposal = {
                "asset": "sol_usdc",
                "amount": 50.0,
                "action": "BUY",
                "chain": "solana"
            }
            try:
                prop_resp = requests.post(f"{LEDGER_URL}/api/v1/propose", json=proposal)
                tx_proposal = prop_resp.json()
                board.post("pending_trade", tx_proposal)
                logger.info("[RiskAgent] Trade posted to bulletin board for compliance review.")
            except Exception as e:
                logger.error(f"[RiskAgent] Proposal failed: {e}")

class ComplianceAgent:
    """Enforces jurisdiction rules and generates ZK proofs."""
    def audit_trade(self, board: CRDTBulletinBoard):
        trade = board.read("pending_trade")
        if not trade:
            return
            
        logger.info(f"[ComplianceAgent] Reviewing trade {trade['tx_id']} against STRICT_L3 policies...")
        
        # Simulate successful audit
        trade["policy_approved"] = True
        trade["audit_hash"] = hashlib.sha256(trade['tx_id'].encode()).hexdigest()
        
        # Phase 7: Generate ZK Proof
        logger.info("[ComplianceAgent] Generating ZK-SNARK alignment proof...")
        trade["zk_proof"] = ProofVerifier.generate_simulated_proof(trade["audit_hash"])
        
        board.post("approved_trade", trade)
        board.post("pending_trade", None) # clear

class ExecutionAgent:
    """Finalizes execution with the ledger."""
    def execute(self, board: CRDTBulletinBoard):
        trade = board.read("approved_trade")
        if not trade:
            return
            
        logger.info("[ExecutionAgent] Consensus reached. Broadcasting payload to ledger.")
        try:
            settle_resp = requests.post(f"{LEDGER_URL}/api/v1/settle", json=trade)
            if settle_resp.status_code == 200:
                logger.info(f"[ExecutionAgent] Settlement confirmed: {settle_resp.json()}")
                self._stream_audit(trade)
            else:
                logger.error(f"[ExecutionAgent] Settlement rejected: {settle_resp.text}")
        except Exception as e:
            logger.error(f"[ExecutionAgent] Execution failed: {e}")
            
        board.post("approved_trade", None) # clear

    def _stream_audit(self, trade: dict):
        try:
            event = {
                "event_type": "SWARM_SETTLEMENT",
                "jurisdiction": os.getenv("SS_JURISDICTION", "local"),
                "details": trade
            }
            requests.post(f"{AUDIT_URL}/audit", json=event)
        except Exception:
            pass

class SovereignSwarm:
    def __init__(self):
        self.board = CRDTBulletinBoard()
        self.risk = RiskAgent()
        self.compliance = ComplianceAgent()
        self.execution = ExecutionAgent()
        
    def run_cycle(self):
        logger.info("--- Swarm Cycle Start ---")
        self.risk.evaluate_markets(self.board)
        self.compliance.audit_trade(self.board)
        self.execution.execute(self.board)
        logger.info("--- Swarm Cycle End ---\n")

if __name__ == "__main__":
    swarm = SovereignSwarm()
    while True:
        swarm.run_cycle()
        time.sleep(15)
