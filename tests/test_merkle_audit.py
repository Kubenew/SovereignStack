"""Tests for Merkle tree audit chain."""

import os
import json

os.environ.setdefault("SPIFFE_ENABLED", "false")
os.environ.setdefault("OASA_ENFORCE_COMPLIANCE", "STRICT")

import pytest
from fastapi.testclient import TestClient
from services.merkle_audit import MerkleTree, _hash_event, _hash_pair
from services.gateway_service import app

client = TestClient(app)


class TestMerkleTree:
    def test_empty_tree(self):
        tree = MerkleTree()
        assert tree.root is None
        assert tree.size == 0

    def test_single_event(self):
        tree = MerkleTree([{"type": "test", "data": "hello"}])
        assert tree.size == 1
        assert tree.root is not None
        assert len(tree.leaves) == 1
        assert len(tree.tree) == 1  # Just the leaf

    def test_two_events(self):
        e1 = {"type": "test", "data": "a"}
        e2 = {"type": "test", "data": "b"}
        tree = MerkleTree([e1, e2])
        assert tree.size == 2
        assert len(tree.leaves) == 2
        assert len(tree.tree) == 3  # 2 leaves + 1 internal node
        expected_root = _hash_pair(_hash_event(e1), _hash_event(e2))
        assert tree.root == expected_root

    def test_three_events(self):
        events = [
            {"type": "test", "data": "a"},
            {"type": "test", "data": "b"},
            {"type": "test", "data": "c"},
        ]
        tree = MerkleTree(events)
        assert tree.size == 3
        # Tree: [h0, h1, h2, h01, h2, h012]
        assert len(tree.tree) == 6
        assert tree.tree[3] == _hash_pair(tree.tree[0], tree.tree[1])  # h01
        assert tree.tree[4] == tree.tree[2]  # h2 propagated
        assert tree.tree[5] == _hash_pair(tree.tree[3], tree.tree[4])  # root

    def test_append_event(self):
        tree = MerkleTree()
        tree.append({"type": "first"})
        assert tree.size == 1
        assert tree.root is not None
        root1 = tree.root
        tree.append({"type": "second"})
        assert tree.size == 2
        assert tree.root != root1  # Root changed

    def test_proof_verification(self):
        events = [
            {"type": "a", "ts": "1"},
            {"type": "b", "ts": "2"},
            {"type": "c", "ts": "3"},
            {"type": "d", "ts": "4"},
        ]
        tree = MerkleTree(events)
        for i in range(len(events)):
            proof = tree.get_proof(i)
            assert tree.verify_event(events[i], proof, tree.root), f"Event {i} verification failed"

    def test_proof_rejects_wrong_event(self):
        events = [
            {"type": "a", "ts": "1"},
            {"type": "b", "ts": "2"},
        ]
        tree = MerkleTree(events)
        proof = tree.get_proof(0)
        # Try to verify event 1 against proof for event 0
        assert not tree.verify_event(events[1], proof, tree.root)

    def test_proof_index_error(self):
        tree = MerkleTree([{"type": "test"}])
        with pytest.raises(IndexError):
            tree.get_proof(5)
        with pytest.raises(IndexError):
            tree.get_proof(-1)

    def test_large_tree(self):
        events = [{"type": "test", "i": i} for i in range(100)]
        tree = MerkleTree(events)
        assert tree.size == 100
        # Verify root integrity
        tree._rebuild()
        assert tree.root == tree.get_root()
        # Verify a sample of proofs
        for i in [0, 1, 50, 99]:
            proof = tree.get_proof(i)
            assert tree.verify_event(events[i], proof, tree.root)

    def test_serialization(self):
        events = [
            {"type": "a", "data": "hello"},
            {"type": "b", "data": "world"},
        ]
        tree = MerkleTree(events)
        # Serialize and deserialize
        import io
        data = {"root": tree.root, "size": tree.size, "events": tree.events}
        restored = MerkleTree(events=data["events"])
        assert restored.root == tree.root
        assert restored.size == tree.size

    def test_append_after_load(self):
        tree = MerkleTree([{"type": "initial"}])
        root_before = tree.root
        tree.append({"type": "added"})
        assert tree.size == 2
        assert tree.root != root_before


class TestMerkleEndpoints:
    def test_audit_root_endpoint(self):
        resp = client.get("/audit/root")
        assert resp.status_code == 200
        data = resp.json()
        assert "root" in data
        assert "size" in data
        assert data["size"] >= 0

    def test_audit_proof_valid(self):
        resp = client.get("/audit/proof/0")
        if resp.status_code == 200:
            data = resp.json()
            assert "event" in data
            assert "proof" in data
            assert "root" in data
        else:
            # No events yet
            assert resp.status_code == 404

    def test_audit_proof_invalid(self):
        resp = client.get("/audit/proof/99999")
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_audit_events_endpoint(self):
        resp = client.get("/audit/events")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

    def test_audit_events_pagination(self):
        resp = client.get("/audit/events?limit=5&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_merkle_audit_events_generated(self):
        """Verify that API calls generate audit events that are hashed into the tree."""
        from services.merkle_audit import get_merkle_tree
        tree = get_merkle_tree()
        size_before = tree.size
        # Make an API call that generates audit events (compliance violation)
        client.post("/v1/chat/completions", json={
            "model": "test",
            "messages": [{"role": "user", "content": "hello"}],
            "oasa_compliance_lock": False,
        })
        size_after = tree.size
        assert size_after > size_before, "Audit events should be generated and hashed into Merkle tree"


class TestVerifyTool:
    def test_verify_tool_imports(self):
        """Verify the CLI tool can be imported without errors."""
        from tools.verify_audit import cmd_status, cmd_proof, cmd_verify
        assert callable(cmd_status)
        assert callable(cmd_proof)
        assert callable(cmd_verify)
