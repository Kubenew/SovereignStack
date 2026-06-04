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
        self.tree: list[list[str]] = []
        self.root: str | None = None
        if self.events:
            self._rebuild()

    def _rebuild(self):
        self.leaves = [_hash_event(e) for e in self.events]
        self.tree = [list(self.leaves)]
        level = 0
        while len(self.tree[level]) > 1:
            next_level = []
            for i in range(0, len(self.tree[level]), 2):
                left = self.tree[level][i]
                if i + 1 < len(self.tree[level]):
                    right = self.tree[level][i + 1]
                    next_level.append(_hash_pair(left, right))
                else:
                    next_level.append(left)
            self.tree.append(next_level)
            level += 1
        self.root = self.tree[-1][0] if self.tree and self.tree[-1] else None

    def append(self, event: dict) -> str:
        self.events.append(event)
        leaf = _hash_event(event)
        self.leaves.append(leaf)
        
        if not self.tree:
            self.tree.append([leaf])
            self.root = leaf
            self._save()
            return leaf
            
        self.tree[0].append(leaf)
        
        # Propagate changes up the right edge
        idx = len(self.tree[0]) - 1
        for level in range(len(self.tree)):
            if level == len(self.tree) - 1 and len(self.tree[level]) > 1:
                # Need a new root level
                self.tree.append([])
                
            if level + 1 < len(self.tree):
                if idx % 2 == 1:
                    # Right child, update the parent by hashing with left sibling
                    left = self.tree[level][idx - 1]
                    right = self.tree[level][idx]
                    parent_hash = _hash_pair(left, right)
                    if idx // 2 < len(self.tree[level + 1]):
                        self.tree[level + 1][idx // 2] = parent_hash
                    else:
                        self.tree[level + 1].append(parent_hash)
                else:
                    # Left child, just carry over or append
                    if idx // 2 < len(self.tree[level + 1]):
                        self.tree[level + 1][idx // 2] = self.tree[level][idx]
                    else:
                        self.tree[level + 1].append(self.tree[level][idx])
            idx //= 2
            
        self.root = self.tree[-1][0] if self.tree and self.tree[-1] else None
        self._save()
        return self.leaves[-1]

    def get_proof(self, event_index: int) -> list[dict]:
        if event_index < 0 or event_index >= len(self.leaves):
            raise IndexError(f"Event index {event_index} out of range (0-{len(self.leaves)-1})")
        proof = []
        idx = event_index
        for level in range(len(self.tree) - 1):
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if sibling_idx < len(self.tree[level]):
                sibling = self.tree[level][sibling_idx]
                position = "right" if idx % 2 == 0 else "left"
                proof.append({"position": position, "hash": sibling})
            idx //= 2
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
