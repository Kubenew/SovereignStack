"""Content hashing utilities.

Thin wrapper around hashlib.sha256, returning ss-core ContentHash types.
"""

from __future__ import annotations

import hashlib

from ss_core.types import ContentHash


def hash_content(data: bytes) -> ContentHash:
    """Hash arbitrary bytes with SHA-256 and return a ContentHash."""
    return ContentHash(digest=hashlib.sha256(data).digest())


def hash_content_hex(data: bytes) -> str:
    """Hash arbitrary bytes with SHA-256 and return the hex digest string."""
    return hashlib.sha256(data).hexdigest()


def hash_concat(*parts: bytes) -> ContentHash:
    """Hash the concatenation of multiple byte strings.

    Useful for Merkle tree node computation: ``hash_concat(left, right)``.
    """
    h = hashlib.sha256()
    for part in parts:
        h.update(part)
    return ContentHash(digest=h.digest())
