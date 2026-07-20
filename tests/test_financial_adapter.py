"""
Tests for the Tokenized Ledger Adapter integration.
"""
import os
import pytest
from examples.financial_adapter.ledger_adapter import LedgerAdapter
from examples.financial_adapter.trading_agent import SovereignTradingAgent

def test_ledger_adapter_initialization():
    adapter = LedgerAdapter("examples/financial_adapter/config.yaml")
    balances = adapter.get_balances()
    assert "tokenized_usdc" in balances
    assert balances["tokenized_usdc"] == 1000000.0

def test_unapproved_transaction_rejected():
    adapter = LedgerAdapter("dummy_config")
    tx = {
        "asset": "tokenized_tsla_bonds",
        "amount": 10.0,
        "action": "BUY",
        "policy_approved": False
    }
    result = adapter.execute_settlement(tx)
    assert result is False

def test_trading_agent_workflow():
    adapter = LedgerAdapter("dummy_config")
    agent = SovereignTradingAgent(adapter)
    
    # Run the agent workflow
    agent.evaluate_risk_and_hedge()
    
    # Assert balances changed correctly (50 bonds bought at 100 each = 5000 usdc spent)
    balances = adapter.get_balances()
    assert balances["tokenized_tsla_bonds"] == 550.0
    assert balances["tokenized_usdc"] == 995000.0
