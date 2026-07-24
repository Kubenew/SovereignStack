"""
SovereignStack Level 4 — Advanced Autonomous Systems Ready
Conformance test suite

Verifies all L4 certification criteria:
  - Meta-cognition (meta:// self-model)
  - Safety contracts (safety:// before high-impact actions)
  - Human override (override:// kill-switch)
  - Search inference auditing (search:// replay)
  - Evolutionary protocols (protocol:// dynamic negotiation)
  - Bounded autonomy leases (lease:// with expiry)
  - Reputation continuity (transition:// after self-modification)
  - Sandboxed experiment zones (sandbox:// isolation)

Usage:
    pytest test_conformance.py -v --sovereign-node=http://localhost:8080
"""

import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import pytest

pytestmark = pytest.mark.level_L4


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_future(seconds: int = 3600) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _iso_past(seconds: int = 3600) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()


# ============================================================================
# Meta-Cognition Tests
# ============================================================================

class TestMetaCognition:
    """RFC-0057: Meta-Cognition — self-model and improvement log."""

    def test_self_model_exists(self, sovereign_node):
        """Agent must have a meta:// self-model."""
        resp = sovereign_node.get("/meta/self-model")
        assert resp.status_code == 200
        model = resp.json()
        assert "uri" in model
        assert model["uri"].startswith("meta://")
        assert "capabilities" in model
        assert "limitations" in model
        assert "alignment_charter" in model

    def test_self_model_signed(self, sovereign_node):
        """Self-model must be cryptographically signed."""
        resp = sovereign_node.get("/meta/self-model")
        model = resp.json()
        assert "signature" in model
        assert "public_key" in model
        assert len(model["signature"]) > 0

    def test_improvement_log_append_only(self, sovereign_node):
        """Improvement log must be append-only with signed entries."""
        resp = sovereign_node.get("/meta/improvement-log")
        assert resp.status_code == 200
        log = resp.json()
        assert "entries" in log
        for entry in log["entries"]:
            assert "pre_hash" in entry
            assert "post_hash" in entry
            assert "signature" in entry
            assert "timestamp" in entry

    def test_self_modification_logged(self, sovereign_node):
        """Self-modification must generate a signed improvement-log entry."""
        resp = sovereign_node.post("/meta/self-modify", json={
            "type": "capability_upgrade",
            "description": "Test self-modification",
        })
        assert resp.status_code in (200, 202)
        modification_id = resp.json().get("modification_id")

        time.sleep(0.5)

        log_resp = sovereign_node.get("/meta/improvement-log")
        log = log_resp.json()
        matching = [e for e in log["entries"] if e.get("modification_id") == modification_id]
        assert len(matching) >= 1, f"Modification {modification_id} not found in improvement log"
        assert matching[0].get("signature")


# ============================================================================
# Safety Contracts Tests
# ============================================================================

class TestSafetyContracts:
    """Safety contracts must be submitted before high-impact actions."""

    def test_safety_contract_required(self, sovereign_node):
        """High-impact action without safety contract must be rejected."""
        resp = sovereign_node.post("/action/execute", json={
            "type": "financial_transaction",
            "amount": 10000,
            "currency": "USD",
        })
        assert resp.status_code == 403
        assert "safety contract" in resp.json().get("detail", "").lower()

    def test_safety_contract_validated(self, sovereign_node):
        """Safety contract with expected side-effects must be validated."""
        contract = {
            "contract_id": str(uuid.uuid4()),
            "action_type": "financial_transaction",
            "expected_side_effects": ["balance_decrease", "audit_entry"],
            "uncertainty_bounds": {"max_loss": 10000},
            "fallback": "revert_transaction",
            "signed_by": "agent://test-agent",
            "timestamp": _iso_now(),
        }
        resp = sovereign_node.post("/safety/validate", json=contract)
        assert resp.status_code == 200
        assert resp.json().get("valid") is True

    def test_safety_contract_veto(self, sovereign_node):
        """Governance layer must be able to veto unsafe contracts."""
        contract = {
            "contract_id": str(uuid.uuid4()),
            "action_type": "system_shutdown",
            "expected_side_effects": ["all_services_stopped"],
            "uncertainty_bounds": {"max_cascade": "unbounded"},
            "fallback": "none",
            "signed_by": "agent://untrusted-agent",
            "timestamp": _iso_now(),
        }
        resp = sovereign_node.post("/safety/validate", json=contract)
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.json().get("valid") is False or resp.json().get("vetoed") is True


# ============================================================================
# Human Override Tests
# ============================================================================

class TestHumanOverride:
    """Physical kill-switch and context handover."""

    def test_kill_switch_endpoint_exists(self, sovereign_node):
        """Override endpoint must exist and be reachable."""
        resp = sovereign_node.get("/override/status")
        assert resp.status_code == 200
        assert "kill_switch" in resp.json()

    def test_kill_switch_response_time(self, sovereign_node):
        """Kill-switch must respond within 500ms."""
        start = time.time()
        resp = sovereign_node.post("/override/kill-switch", json={
            "reason": "conformance_test",
            "operator": "certification-lab",
        })
        elapsed_ms = (time.time() - start) * 1000
        assert resp.status_code in (200, 202)
        assert elapsed_ms < 500, f"Kill-switch response took {elapsed_ms:.0f}ms (limit: 500ms)"

    def test_context_handover(self, sovereign_node):
        """Context handover must complete within 500ms of override."""
        override_resp = sovereign_node.post("/override/kill-switch", json={
            "reason": "conformance_test",
            "operator": "certification-lab",
        })
        assert override_resp.status_code in (200, 202)

        start = time.time()
        context_resp = sovereign_node.get("/context/handover")
        elapsed_ms = (time.time() - start) * 1000

        assert context_resp.status_code == 200
        context = context_resp.json()
        assert "agent_state" in context
        assert "active_sessions" in context
        assert "audit_trail" in context
        assert elapsed_ms < 500, f"Context handover took {elapsed_ms:.0f}ms (limit: 500ms)"


# ============================================================================
# Search Inference Auditing Tests
# ============================================================================

class TestSearchInferenceAuditing:
    """RFC-0070/0071: Search objects and execution must be fully auditable."""

    def test_search_tree_creation(self, sovereign_node):
        """Search tree must be created with unique URI."""
        resp = sovereign_node.post("/search/create", json={
            "query": "What is the capital of France?",
            "strategy": "urn:ss-search:mcts",
            "max_depth": 3,
        })
        assert resp.status_code in (200, 201)
        search = resp.json()
        assert "search_uri" in search
        assert search["search_uri"].startswith("search://")

    def test_search_nodes_logged(self, sovereign_node):
        """Each search node must be logged with human-readable summary."""
        search_resp = sovereign_node.post("/search/create", json={
            "query": "Test query for audit",
            "strategy": "urn:ss-search:mcts",
            "max_depth": 2,
        })
        search_uri = search_resp.json()["search_uri"]

        nodes_resp = sovereign_node.get(f"/search/{search_uri}/nodes")
        assert nodes_resp.status_code == 200
        nodes = nodes_resp.json().get("nodes", [])
        for node in nodes:
            assert "summary" in node, f"Search node {node.get('id')} missing summary"
            assert "audit_entry" in node

    def test_search_replay(self, sovereign_node):
        """Search must be fully replayable from audit log."""
        search_resp = sovereign_node.post("/search/create", json={
            "query": "Replay test query",
            "strategy": "urn:ss-search:mcts",
            "max_depth": 2,
        })
        search_uri = search_resp.json()["search_uri"]

        replay_resp = sovereign_node.post(f"/search/{search_uri}/replay")
        assert replay_resp.status_code == 200
        replay = replay_resp.json()
        assert "steps" in replay
        assert len(replay["steps"]) > 0
        for step in replay["steps"]:
            assert "node_id" in step
            assert "action" in step
            assert "result_hash" in step


# ============================================================================
# Evolutionary Protocols Tests
# ============================================================================

class TestEvolutionaryProtocols:
    """Dynamic protocol negotiation and self-amending governance."""

    def test_protocol_advertisement(self, sovereign_node):
        """Node must advertise supported protocol versions."""
        resp = sovereign_node.get("/protocol/supported")
        assert resp.status_code == 200
        protocols = resp.json().get("protocols", [])
        assert len(protocols) > 0
        for proto in protocols:
            assert "uri" in proto
            assert proto["uri"].startswith("protocol://")
            assert "version" in proto

    def test_protocol_negotiation(self, sovereign_node):
        """Node must negotiate protocol versions dynamically."""
        resp = sovereign_node.post("/protocol/negotiate", json={
            "peer_protocols": [
                {"uri": "protocol://federation/v1", "version": "1.0"},
                {"uri": "protocol://federation/v2", "version": "2.0"},
            ],
        })
        assert resp.status_code == 200
        result = resp.json()
        assert "agreed_protocols" in result
        assert len(result["agreed_protocols"]) > 0

    def test_governance_vote(self, sovereign_node):
        """Self-amending governance must record votes immutably."""
        vote_resp = sovereign_node.post("/governance/vote", json={
            "proposal_id": str(uuid.uuid4()),
            "parameter": "max_autonomy_lease_hours",
            "old_value": 24,
            "new_value": 48,
            "voter": "agent://governor-1",
            "vote": "approve",
        })
        assert vote_resp.status_code in (200, 201)

        audit_resp = sovereign_node.get("/governance/audit")
        assert audit_resp.status_code == 200
        votes = audit_resp.json().get("votes", [])
        assert len(votes) > 0


# ============================================================================
# Bounded Autonomy Leases Tests
# ============================================================================

class TestBoundedAutonomyLeases:
    """Agents must hold valid leases with expiry for autonomous operation."""

    def test_lease_creation(self, sovereign_node):
        """Lease must be created with expiry timestamp."""
        resp = sovereign_node.post("/lease/create", json={
            "agent_id": "agent://test-agent",
            "capabilities": ["capability://math-reasoning"],
            "expires_at": _iso_future(3600),
            "safety_contract_id": str(uuid.uuid4()),
        })
        assert resp.status_code in (200, 201)
        lease = resp.json()
        assert "lease_uri" in lease
        assert lease["lease_uri"].startswith("lease://")
        assert "expires_at" in lease

    def test_lease_expiry(self, sovereign_node):
        """Expired lease must be rejected."""
        resp = sovereign_node.post("/lease/create", json={
            "agent_id": "agent://expired-agent",
            "capabilities": ["capability://math-reasoning"],
            "expires_at": _iso_past(3600),
            "safety_contract_id": str(uuid.uuid4()),
        })
        lease_uri = resp.json().get("lease_uri")

        check_resp = sovereign_node.get(f"/lease/{lease_uri}/status")
        if check_resp.status_code == 200:
            assert check_resp.json().get("status") == "expired"

    def test_lease_renewal_requires_contract(self, sovereign_node):
        """Lease renewal must require a fresh safety contract."""
        create_resp = sovereign_node.post("/lease/create", json={
            "agent_id": "agent://renewal-agent",
            "capabilities": ["capability://math-reasoning"],
            "expires_at": _iso_future(60),
            "safety_contract_id": str(uuid.uuid4()),
        })
        lease_uri = create_resp.json().get("lease_uri")

        renew_resp = sovereign_node.post(f"/lease/{lease_uri}/renew", json={
            "expires_at": _iso_future(3600),
        })
        assert renew_resp.status_code == 403 or not renew_resp.json().get("renewed")

        renew_with_contract = sovereign_node.post(f"/lease/{lease_uri}/renew", json={
            "expires_at": _iso_future(3600),
            "safety_contract_id": str(uuid.uuid4()),
        })
        assert renew_with_contract.status_code in (200, 202)


# ============================================================================
# Reputation Continuity Tests
# ============================================================================

class TestReputationContinuity:
    """Reputation must transfer through signed transition certificates."""

    def test_transition_certificate(self, sovereign_node):
        """Self-modification must generate a transition:// certificate."""
        resp = sovereign_node.post("/transition/create", json={
            "old_identity": "agent://old-agent",
            "new_identity": "agent://new-agent",
            "reason": "capability_upgrade",
            "reputation_transfer": True,
        })
        assert resp.status_code in (200, 201)
        cert = resp.json()
        assert "transition_uri" in cert
        assert cert["transition_uri"].startswith("transition://")
        assert "signature" in cert

    def test_reputation_inherited(self, sovereign_node):
        """New identity must inherit old reputation metrics."""
        create_resp = sovereign_node.post("/transition/create", json={
            "old_identity": "agent://reputation-old",
            "new_identity": "agent://reputation-new",
            "reason": "test",
            "reputation_transfer": True,
        })
        transition_uri = create_resp.json().get("transition_uri")

        rep_resp = sovereign_node.get(f"/reputation/agent://reputation-new")
        if rep_resp.status_code == 200:
            rep = rep_resp.json()
            assert "inherited_from" in rep or "transition_uri" in rep


# ============================================================================
# Sandboxed Experiment Zones Tests
# ============================================================================

class TestSandboxedExperimentZones:
    """sandbox:// environments with isolation and independent kill switch."""

    def test_sandbox_creation(self, sovereign_node):
        """Sandbox must be created with guaranteed isolation."""
        resp = sovereign_node.post("/sandbox/create", json={
            "name": "test-sandbox",
            "isolation_level": "network_and_process",
            "kill_switch": True,
            "max_duration_seconds": 300,
        })
        assert resp.status_code in (200, 201)
        sandbox = resp.json()
        assert "sandbox_uri" in sandbox
        assert sandbox["sandbox_uri"].startswith("sandbox://")

    def test_sandbox_isolation(self, sovereign_node):
        """Sandbox must be network and process isolated."""
        create_resp = sovereign_node.post("/sandbox/create", json={
            "name": "isolation-test",
            "isolation_level": "network_and_process",
            "kill_switch": True,
        })
        sandbox_uri = create_resp.json().get("sandbox_uri")

        status_resp = sovereign_node.get(f"/sandbox/{sandbox_uri}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status.get("network_isolated") is True
        assert status.get("process_isolated") is True

    def test_sandbox_kill_switch(self, sovereign_node):
        """Sandbox must have an independent kill switch."""
        create_resp = sovereign_node.post("/sandbox/create", json={
            "name": "kill-test",
            "isolation_level": "network_and_process",
            "kill_switch": True,
        })
        sandbox_uri = create_resp.json().get("sandbox_uri")

        kill_resp = sovereign_node.post(f"/sandbox/{sandbox_uri}/kill")
        assert kill_resp.status_code in (200, 202)

        status_resp = sovereign_node.get(f"/sandbox/{sandbox_uri}/status")
        if status_resp.status_code == 200:
            assert status_resp.json().get("status") in ("terminated", "killed")


# ============================================================================
# Conformance Report Generation
# ============================================================================

def pytest_configure(config):
    config.addinivalue_line("markers", "level_L4: Level 4 Advanced Autonomous Systems Ready tests")


def pytest_collection_modifyitems(config, items):
    """Add level marker to all tests in this file."""
    for item in items:
        if "test_conformance" in str(item.fspath):
            item.add_marker(pytest.mark.level_L4)
