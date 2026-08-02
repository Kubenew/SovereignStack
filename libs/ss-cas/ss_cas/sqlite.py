"""SQLite-backed Content-Addressed Storage.

Uses WAL (Write-Ahead Logging) mode for concurrent read performance.
Single table, no ORM, raw sqlite3 module. Zero external dependencies.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ss_core.errors import StorageError
from ss_core.types import ContentHash
from ss_crypto.hashing import hash_content


class SqliteCAS:
    """Content-addressed store backed by a SQLite database.

    The database uses WAL mode for high concurrent read throughput.
    All writes are serialized by SQLite's internal locking.

    Args:
        db_path: Path to the SQLite database file. Use ``:memory:`` for testing.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the objects table if it doesn't exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                hash    BLOB PRIMARY KEY,
                data    BLOB NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def put(self, data: bytes) -> ContentHash:
        """Store data and return its content hash.

        Idempotent: storing the same data twice is a no-op.
        """
        content_hash = hash_content(data)
        now = datetime.now(timezone.utc).isoformat()

        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO objects (hash, data, created_at) VALUES (?, ?, ?)",
                (content_hash.digest, data, now),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to store object: {e}") from e

        return content_hash

    def get(self, content_hash: ContentHash) -> bytes | None:
        """Retrieve data by its content hash, or None if not found."""
        try:
            row = self._conn.execute(
                "SELECT data FROM objects WHERE hash = ?",
                (content_hash.digest,),
            ).fetchone()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve object: {e}") from e

        return row[0] if row else None

    def exists(self, content_hash: ContentHash) -> bool:
        """Check if an object exists in the store."""
        try:
            row = self._conn.execute(
                "SELECT 1 FROM objects WHERE hash = ? LIMIT 1",
                (content_hash.digest,),
            ).fetchone()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to check object existence: {e}") from e

        return row is not None

    def count(self) -> int:
        """Return the total number of objects stored."""
        row = self._conn.execute("SELECT COUNT(*) FROM objects").fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> SqliteCAS:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"SqliteCAS(db_path={self._db_path!r})"
