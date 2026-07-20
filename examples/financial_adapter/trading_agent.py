"""
Autonomous Trading Agent for the Sovereign Mesh.
Communicates via HTTP to the Mock Ledger and streams audits to the Mesh Aggregator.
"""
import logging
import requests
import json
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingAgent")

LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8545")
AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:9091")

class SovereignTradingAgent:
    def __init__(self):
        logger.info(f"Initialized SovereignTradingAgent pointing to Ledger: {LEDGER_URL}")

    def evaluate_risk_and_hedge(self):
        """
        Agent reasoning loop
        """
        try:
            resp = requests.get(f"{LEDGER_URL}/api/v1/balances")
            balances = resp.json()
            logger.info(f"Agent perceived state: {balances}")
        except Exception as e:
            logger.error(f"Failed to read from ledger: {e}")
            return
        
        if balances.get("tokenized_usdc", 0) > 500000:
            logger.info("Reasoning: Excess liquidity detected. Initiating hedge strategy.")
            
            tx_req = {
                "asset": "tokenized_tsla_bonds",
                "amount": 50.0,
                "action": "BUY"
            }
            try:
                prop_resp = requests.post(f"{LEDGER_URL}/api/v1/propose", json=tx_req)
                tx_proposal = prop_resp.json()
            except Exception as e:
                logger.error(f"Failed to propose transaction: {e}")
                return

            signed_tx = self._enforce_policy(tx_proposal)
            
            if signed_tx:
                try:
                    settle_resp = requests.post(f"{LEDGER_URL}/api/v1/settle", json=signed_tx)
                    logger.info(f"Settlement response: {settle_resp.json()}")
                    self._log_audit(signed_tx)
                except Exception as e:
                    logger.error(f"Failed to settle transaction: {e}")

    def _enforce_policy(self, tx_proposal: dict) -> dict:
        """
        Simulates the ss-policy engine evaluating the transaction against STRICT_L3 rules.
        """
        logger.info("ss-policy: Auditing proposed transaction against jurisdiction rules...")
        tx_proposal["policy_approved"] = True
        tx_proposal["audit_hash"] = "0xABC123"
        logger.info("ss-policy: Transaction approved and signed.")
        return tx_proposal

    def _log_audit(self, signed_tx: dict):
        """
        Streams the audit event to the mesh audit-aggregator.
        """
        try:
            # We wrap the transaction in an audit event
            event = {
                "event_type": "FINANCIAL_SETTLEMENT",
                "jurisdiction": os.getenv("SS_JURISDICTION", "local"),
                "details": signed_tx
            }
            # Fire and forget mock audit logging
            # The actual aggregator might expect a different schema, but we'll POST for demo
            requests.post(f"{AUDIT_URL}/audit", json=event)
            logger.info("Audit logged to mesh aggregator successfully.")
        except Exception as e:
            # Not failing the agent if audit fails in demo, but logged
            logger.warning(f"Could not reach audit aggregator (mocking success for standalone runs): {e}")

if __name__ == "__main__":
    agent = SovereignTradingAgent()
    while True:
        agent.evaluate_risk_and_hedge()
        time.sleep(30)
