import hashlib
import json
import os
import logging

logger = logging.getLogger(__name__)

AUDIT_DIR = os.getenv("DATA_DIR", "/app/data")
MERKLE_PATH = os.path.join(AUDIT_DIR, "merkle_tree.json")


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _serialize_event(event: dict) -> bytes:
    return json.dumps(event, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _hash_event(event: dict) -> str:
    return _hash_bytes(_serialize_event(event))


def _hash_pair(left: str, right: str) -> str:
    return _hash_bytes((left + right).encode("ascii"))


class MerkleTree:
    """Append-only Merkle tree for tamper-evident audit logging.

    Stores the full event list and tree structure in memory.
    Persists to disk on every append for crash recovery.
    """

    def __init__(self, events: list[dict] | None = None):
        self.events: list[dict] = events or []
        self.leaves: list[str] = []
        self.tree: list[str | None] = []
        self.root: str | None = None
        if self.events:
            self._rebuild()

    def _rebuild(self):
        self.leaves = [_hash_event(e) for e in self.events]
        self.tree = list(self.leaves)
        level_start = 0
        level_size = len(self.tree)
        while level_size > 1:
            for i in range(0, level_size, 2):
                left = self.tree[level_start + i]
                if i + 1 < level_size:
                    right = self.tree[level_start + i + 1]
                    self.tree.append(_hash_pair(left, right))
                else:
                    self.tree.append(left)
            level_start += level_size
            level_size = (level_size + 1) // 2
        self.root = self.tree[-1] if self.tree else None

    def _first_at_level(self, level: int) -> int:
        """Return the index of the first node at a given level (0 = leaves)."""
        idx = 0
        size = len(self.leaves)
        for _ in range(level):
            idx += size
            size = (size + 1) // 2
        return idx

    def append(self, event: dict) -> str:
        self.events.append(event)
        self._rebuild()
        self._save()
        return self.leaves[-1]

    def get_proof(self, event_index: int) -> list[dict]:
        if event_index < 0 or event_index >= len(self.leaves):
            raise IndexError(f"Event index {event_index} out of range (0-{len(self.leaves)-1})")
        proof = []
        idx = event_index
        offset = 0
        size = len(self.leaves)
        while size > 1:
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if sibling_idx < size:
                sibling = self.tree[offset + sibling_idx]
                position = "right" if idx % 2 == 0 else "left"
                proof.append({"position": position, "hash": sibling})
            idx //= 2
            offset += size
            size = (size + 1) // 2
        return proof

    def verify_proof(self, leaf_hash: str, proof: list[dict], root: str) -> bool:
        current = leaf_hash
        for step in proof:
            if step["position"] == "left":
                current = _hash_pair(step["hash"], current)
            else:
                current = _hash_pair(current, step["hash"])
        return current == root

    def verify_event(self, event: dict, proof: list[dict], root: str) -> bool:
        return self.verify_proof(_hash_event(event), proof, root)

    @property
    def size(self) -> int:
        return len(self.leaves)

    def get_root(self) -> str | None:
        return self.root

    def get_event(self, index: int) -> dict | None:
        if 0 <= index < len(self.events):
            return self.events[index]
        return None

    def _save(self):
        try:
            os.makedirs(os.path.dirname(MERKLE_PATH), exist_ok=True)
            data = {
                "root": self.root,
                "size": self.size,
                "events": self.events,
            }
            with open(MERKLE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("Failed to save merkle tree: %s", e)

    @classmethod
    def load(cls) -> "MerkleTree":
        if os.path.exists(MERKLE_PATH):
            try:
                with open(MERKLE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(events=data.get("events", []))
            except Exception as e:
                logger.warning("Failed to load merkle tree: %s", e)
        return cls()


# Global singleton
_merkle_tree: MerkleTree | None = None


def get_merkle_tree() -> MerkleTree:
    global _merkle_tree
    if _merkle_tree is None:
        _merkle_tree = MerkleTree.load()
    return _merkle_tree


def append_event(event: dict) -> str:
    tree = get_merkle_tree()
    return tree.append(event)


def get_current_root() -> str | None:
    return get_merkle_tree().get_root()


def get_proof_for_event(index: int) -> list[dict]:
    return get_merkle_tree().get_proof(index)


def get_tree_size() -> int:
    return get_merkle_tree().size
