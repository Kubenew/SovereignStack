"""Tests for ss-cas: SQLite CAS, Merkle tree, and proofs."""

import pytest

from ss_core.types import ContentHash
from ss_crypto.hashing import hash_content
from ss_cas.sqlite import SqliteCAS
from ss_cas.merkle import MerkleLog
from ss_cas.proof import MerkleProof, Direction


class TestSqliteCAS:
    def test_put_and_get(self):
        with SqliteCAS() as store:
            data = b"hello world"
            h = store.put(data)
            assert store.get(h) == data

    def test_get_nonexistent_returns_none(self):
        with SqliteCAS() as store:
            h = hash_content(b"does not exist")
            assert store.get(h) is None

    def test_exists(self):
        with SqliteCAS() as store:
            data = b"test"
            h = store.put(data)
            assert store.exists(h)
            assert not store.exists(hash_content(b"other"))

    def test_put_idempotent(self):
        with SqliteCAS() as store:
            data = b"same data"
            h1 = store.put(data)
            h2 = store.put(data)
            assert h1 == h2
            assert store.count() == 1

    def test_count(self):
        with SqliteCAS() as store:
            assert store.count() == 0
            store.put(b"a")
            store.put(b"b")
            assert store.count() == 2

    def test_content_hash_matches(self):
        with SqliteCAS() as store:
            data = b"verify hash"
            h = store.put(data)
            expected = hash_content(data)
            assert h == expected


class TestMerkleLog:
    def test_append_and_size(self):
        with MerkleLog() as log:
            assert log.size == 0
            log.append(b"first")
            assert log.size == 1
            log.append(b"second")
            assert log.size == 2

    def test_append_returns_hash_and_index(self):
        with MerkleLog() as log:
            h, idx = log.append(b"data")
            assert isinstance(h, ContentHash)
            assert idx == 0

            h2, idx2 = log.append(b"more")
            assert idx2 == 1

    def test_get_leaf(self):
        with MerkleLog() as log:
            log.append(b"alpha")
            log.append(b"beta")

            result = log.get_leaf(0)
            assert result is not None
            leaf_hash, raw_data = result
            assert raw_data == b"alpha"

            result2 = log.get_leaf(1)
            assert result2 is not None
            assert result2[1] == b"beta"

    def test_get_leaf_out_of_range(self):
        with MerkleLog() as log:
            assert log.get_leaf(0) is None

    def test_root_empty_tree(self):
        with MerkleLog() as log:
            root = log.root()
            assert isinstance(root, ContentHash)

    def test_root_single_leaf(self):
        with MerkleLog() as log:
            h, _ = log.append(b"only leaf")
            assert log.root() == h

    def test_root_two_leaves(self):
        with MerkleLog() as log:
            h1, _ = log.append(b"left")
            h2, _ = log.append(b"right")
            root = log.root()
            # Root should be hash(h1 || h2)
            from ss_crypto.hashing import hash_concat
            expected = hash_concat(h1.digest, h2.digest)
            assert root == expected

    def test_root_deterministic(self):
        with MerkleLog() as log:
            log.append(b"a")
            log.append(b"b")
            log.append(b"c")
            r1 = log.root()
            r2 = log.root()
            assert r1 == r2

    def test_root_changes_on_append(self):
        with MerkleLog() as log:
            log.append(b"a")
            r1 = log.root()
            log.append(b"b")
            r2 = log.root()
            assert r1 != r2

    def test_prove_single_leaf(self):
        with MerkleLog() as log:
            log.append(b"only")
            proof = log.prove(0)
            assert proof.leaf_index == 0
            assert proof.tree_size == 1
            assert proof.verify()

    def test_prove_two_leaves(self):
        with MerkleLog() as log:
            log.append(b"left")
            log.append(b"right")

            proof0 = log.prove(0)
            assert proof0.verify()

            proof1 = log.prove(1)
            assert proof1.verify()

    def test_prove_many_leaves(self):
        with MerkleLog() as log:
            for i in range(10):
                log.append(f"leaf-{i}".encode())

            for i in range(10):
                proof = log.prove(i)
                assert proof.verify(), f"Proof failed for leaf {i}"

    def test_prove_power_of_two_leaves(self):
        with MerkleLog() as log:
            for i in range(8):
                log.append(f"leaf-{i}".encode())

            for i in range(8):
                proof = log.prove(i)
                assert proof.verify(), f"Proof failed for leaf {i}"

    def test_prove_out_of_range_raises(self):
        with MerkleLog() as log:
            log.append(b"a")
            with pytest.raises(Exception):
                log.prove(1)
            with pytest.raises(Exception):
                log.prove(-1)

    def test_proof_json_roundtrip(self):
        with MerkleLog() as log:
            for i in range(5):
                log.append(f"leaf-{i}".encode())

            proof = log.prove(2)
            json_str = proof.to_json()
            restored = MerkleProof.from_json(json_str)

            assert restored.leaf_index == proof.leaf_index
            assert restored.leaf_hash == proof.leaf_hash
            assert restored.root_hash == proof.root_hash
            assert restored.verify()

    def test_tampered_proof_fails(self):
        with MerkleLog() as log:
            for i in range(4):
                log.append(f"leaf-{i}".encode())

            proof = log.prove(1)
            # Tamper with the root hash
            tampered = MerkleProof(
                leaf_index=proof.leaf_index,
                leaf_hash=proof.leaf_hash,
                steps=proof.steps,
                root_hash=hash_content(b"fake root"),
                tree_size=proof.tree_size,
            )
            assert not tampered.verify()

    def test_verify_proof_static(self):
        with MerkleLog() as log:
            for i in range(6):
                log.append(f"leaf-{i}".encode())

            proof = log.prove(3)
            # Static verification — no tree access needed
            assert MerkleLog.verify_proof(proof)

    def test_odd_number_of_leaves(self):
        """Odd leaf counts test the promotion logic."""
        with MerkleLog() as log:
            for i in range(7):
                log.append(f"leaf-{i}".encode())

            for i in range(7):
                proof = log.prove(i)
                assert proof.verify(), f"Proof failed for leaf {i} (7-leaf tree)"

    def test_large_tree(self):
        """Stress test with 100 leaves."""
        with MerkleLog() as log:
            for i in range(100):
                log.append(f"entry-{i:04d}".encode())

            # Verify a sample of proofs
            for i in [0, 1, 49, 50, 98, 99]:
                proof = log.prove(i)
                assert proof.verify(), f"Proof failed for leaf {i} (100-leaf tree)"
