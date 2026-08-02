"""Append-only Merkle log.

An ordered, tamper-evident log where each entry is a leaf in a binary
Merkle tree. The tree is stored as a flat array of hashes, enabling
efficient append, root computation, and inclusion proof generation.

The implementation follows the RFC 6962 (Certificate Transparency) approach
to Merkle trees: a balanced binary tree built bottom-up, with the tree
growing rightward as new leaves are appended.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ss_core.errors import MerkleError
from ss_core.types import ContentHash
from ss_crypto.hashing import hash_content, hash_concat

from ss_cas.proof import Direction, MerkleProof, ProofStep


class MerkleLog:
    """An append-only Merkle log backed by SQLite.

    Each leaf is a SHA-256 hash of the appended data. Internal nodes
    are computed on-the-fly when generating proofs or the root hash.

    Args:
        db_path: Path to the SQLite database. Use ``:memory:`` for testing.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the leaves table if it doesn't exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS leaves (
                idx         INTEGER PRIMARY KEY AUTOINCREMENT,
                leaf_hash   BLOB NOT NULL,
                raw_data    BLOB NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def append(self, data: bytes) -> tuple[ContentHash, int]:
        """Append data to the log.

        Args:
            data: Arbitrary bytes to append as a new leaf.

        Returns:
            Tuple of (leaf_hash, 0-based index of the new leaf).
        """
        leaf_hash = hash_content(data)
        now = datetime.now(timezone.utc).isoformat()

        cursor = self._conn.execute(
            "INSERT INTO leaves (leaf_hash, raw_data, created_at) VALUES (?, ?, ?)",
            (leaf_hash.digest, data, now),
        )
        self._conn.commit()

        # SQLite AUTOINCREMENT starts at 1, convert to 0-based
        index = cursor.lastrowid - 1
        return leaf_hash, index

    @property
    def size(self) -> int:
        """Number of leaves in the log."""
        row = self._conn.execute("SELECT COUNT(*) FROM leaves").fetchone()
        return row[0] if row else 0

    def get_leaf(self, index: int) -> tuple[ContentHash, bytes] | None:
        """Retrieve a leaf by its 0-based index.

        Returns:
            Tuple of (leaf_hash, raw_data), or None if index is out of range.
        """
        # idx in DB is 1-based (AUTOINCREMENT)
        row = self._conn.execute(
            "SELECT leaf_hash, raw_data FROM leaves WHERE idx = ?",
            (index + 1,),
        ).fetchone()

        if row is None:
            return None

        return ContentHash(digest=row[0]), row[1]

    def _get_all_leaf_hashes(self) -> list[ContentHash]:
        """Load all leaf hashes in order. Used for root/proof computation."""
        rows = self._conn.execute(
            "SELECT leaf_hash FROM leaves ORDER BY idx"
        ).fetchall()
        return [ContentHash(digest=row[0]) for row in rows]

    def root(self) -> ContentHash:
        """Compute the current Merkle root hash.

        For an empty tree, returns the hash of an empty byte string.
        For a single leaf, returns that leaf's hash.
        For multiple leaves, builds the tree bottom-up.
        """
        leaves = self._get_all_leaf_hashes()

        if not leaves:
            return hash_content(b"")

        if len(leaves) == 1:
            return leaves[0]

        return self._compute_root(leaves)

    @staticmethod
    def _compute_root(leaf_hashes: list[ContentHash]) -> ContentHash:
        """Build the Merkle tree bottom-up and return the root.

        If the number of nodes at any level is odd, the last node
        is promoted to the next level (RFC 6962 style).
        """
        level = list(leaf_hashes)

        while len(level) > 1:
            next_level: list[ContentHash] = []
            for i in range(0, len(level), 2):
                if i + 1 < len(level):
                    parent = hash_concat(level[i].digest, level[i + 1].digest)
                    next_level.append(parent)
                else:
                    # Odd node promoted
                    next_level.append(level[i])
            level = next_level

        return level[0]

    def prove(self, index: int) -> MerkleProof:
        """Generate an inclusion proof for the leaf at the given index.

        Args:
            index: 0-based index of the leaf.

        Returns:
            A MerkleProof that can be verified independently.

        Raises:
            MerkleError: If the index is out of range.
        """
        leaves = self._get_all_leaf_hashes()

        if index < 0 or index >= len(leaves):
            raise MerkleError(
                f"Leaf index {index} out of range [0, {len(leaves)})"
            )

        root = self._compute_root(leaves) if len(leaves) > 1 else leaves[0]
        steps = self._build_proof_steps(leaves, index)

        return MerkleProof(
            leaf_index=index,
            leaf_hash=leaves[index],
            steps=steps,
            root_hash=root,
            tree_size=len(leaves),
        )

    @staticmethod
    def _build_proof_steps(
        leaf_hashes: list[ContentHash], target_index: int
    ) -> list[ProofStep]:
        """Build the sibling path from a leaf to the root."""
        steps: list[ProofStep] = []
        level = list(leaf_hashes)
        idx = target_index

        while len(level) > 1:
            if idx % 2 == 0:
                # Target is a left child; sibling is on the right
                if idx + 1 < len(level):
                    steps.append(ProofStep(
                        sibling_hash=level[idx + 1],
                        direction=Direction.RIGHT,
                    ))
                # else: odd node, no sibling — promoted directly
            else:
                # Target is a right child; sibling is on the left
                steps.append(ProofStep(
                    sibling_hash=level[idx - 1],
                    direction=Direction.LEFT,
                ))

            # Move up one level
            next_level: list[ContentHash] = []
            for i in range(0, len(level), 2):
                if i + 1 < len(level):
                    parent = hash_concat(level[i].digest, level[i + 1].digest)
                    next_level.append(parent)
                else:
                    next_level.append(level[i])
            level = next_level
            idx = idx // 2

        return steps

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """Verify a Merkle inclusion proof.

        This is a static method: it needs no access to the tree.
        An auditor can call this with only the proof and no other data.
        """
        return proof.verify()

    def get_leaves_in_range(
        self, start_time: str | None = None, end_time: str | None = None
    ) -> list[tuple[int, ContentHash, bytes]]:
        """Retrieve leaves within a time range.

        Args:
            start_time: ISO 8601 start time (inclusive). None = beginning.
            end_time: ISO 8601 end time (inclusive). None = now.

        Returns:
            List of (index, leaf_hash, raw_data) tuples.
        """
        query = "SELECT idx, leaf_hash, raw_data FROM leaves WHERE 1=1"
        params: list[str] = []

        if start_time:
            query += " AND created_at >= ?"
            params.append(start_time)
        if end_time:
            query += " AND created_at <= ?"
            params.append(end_time)

        query += " ORDER BY idx"
        rows = self._conn.execute(query, params).fetchall()

        return [
            (row[0] - 1, ContentHash(digest=row[1]), row[2])
            for row in rows
        ]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> MerkleLog:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
