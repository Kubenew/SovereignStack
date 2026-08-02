"""ss-cas: Content-Addressed Storage and append-only Merkle tree for SovereignStack."""

from ss_cas.store import ContentStore
from ss_cas.sqlite import SqliteCAS
from ss_cas.merkle import MerkleLog
from ss_cas.proof import MerkleProof

__version__ = "0.1.0"

__all__ = [
    "ContentStore",
    "SqliteCAS",
    "MerkleLog",
    "MerkleProof",
]
