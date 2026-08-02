"""Content-Addressed Storage protocol.

Defines the abstract interface that all CAS backends must implement.
The contract is simple: store bytes by their SHA-256 hash, retrieve by hash.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ss_core.types import ContentHash


@runtime_checkable
class ContentStore(Protocol):
    """Abstract interface for content-addressed storage.

    Implementations must be safe for concurrent reads.
    Write concurrency depends on the backend (SQLite uses WAL mode).
    """

    def put(self, data: bytes) -> ContentHash:
        """Store data and return its content hash.

        If the data already exists (same hash), this is a no-op
        and returns the existing hash.

        Args:
            data: Arbitrary bytes to store.

        Returns:
            The SHA-256 ContentHash of the stored data.
        """
        ...

    def get(self, content_hash: ContentHash) -> bytes | None:
        """Retrieve data by its content hash.

        Args:
            content_hash: The SHA-256 hash of the desired data.

        Returns:
            The stored bytes, or None if not found.
        """
        ...

    def exists(self, content_hash: ContentHash) -> bool:
        """Check if data with the given hash exists in the store.

        Args:
            content_hash: The hash to check.

        Returns:
            True if the data exists.
        """
        ...

    def count(self) -> int:
        """Return the total number of objects in the store."""
        ...
