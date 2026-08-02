"""Merkle inclusion and consistency proofs.

A MerkleProof is a portable, JSON-serializable proof that a specific
leaf exists at a given index in a Merkle tree with a known root.
The verifier only needs the proof, the leaf data, and the root hash —
no access to the full tree is required.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self

from ss_core.types import ContentHash
from ss_crypto.hashing import hash_content, hash_concat


class Direction(Enum):
    """Which side the sibling hash goes on when recomputing the parent."""
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class ProofStep:
    """One step in a Merkle proof: a sibling hash and which side it goes on."""
    sibling_hash: ContentHash
    direction: Direction


@dataclass(frozen=True, slots=True)
class MerkleProof:
    """A Merkle inclusion proof for a single leaf.

    Attributes:
        leaf_index: The 0-based index of the leaf in the tree.
        leaf_hash: The SHA-256 hash of the leaf data.
        steps: The path of sibling hashes from leaf to root.
        root_hash: The expected root hash at the time the proof was generated.
        tree_size: The number of leaves in the tree when the proof was generated.
    """

    leaf_index: int
    leaf_hash: ContentHash
    steps: list[ProofStep] = field(default_factory=list)
    root_hash: ContentHash = field(default_factory=lambda: ContentHash(b"\x00" * 32))
    tree_size: int = 0

    def verify(self) -> bool:
        """Verify the proof by recomputing the root from the leaf.

        Returns:
            True if the recomputed root matches the expected root_hash.
        """
        current = self.leaf_hash
        for step in self.steps:
            if step.direction == Direction.LEFT:
                # Sibling is on the left
                current = hash_concat(step.sibling_hash.digest, current.digest)
            else:
                # Sibling is on the right
                current = hash_concat(current.digest, step.sibling_hash.digest)
        return current == self.root_hash

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "leaf_index": self.leaf_index,
            "leaf_hash": str(self.leaf_hash),
            "root_hash": str(self.root_hash),
            "tree_size": self.tree_size,
            "steps": [
                {
                    "sibling_hash": str(s.sibling_hash),
                    "direction": s.direction.value,
                }
                for s in self.steps
            ],
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from a dictionary."""
        steps = [
            ProofStep(
                sibling_hash=ContentHash.from_prefixed(s["sibling_hash"]),
                direction=Direction(s["direction"]),
            )
            for s in data["steps"]
        ]
        return cls(
            leaf_index=data["leaf_index"],
            leaf_hash=ContentHash.from_prefixed(data["leaf_hash"]),
            root_hash=ContentHash.from_prefixed(data["root_hash"]),
            tree_size=data["tree_size"],
            steps=steps,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
