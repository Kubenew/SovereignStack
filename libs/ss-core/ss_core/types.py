"""Foundational types used across all SovereignStack libraries.

These are thin wrappers (newtypes) around raw bytes/strings to provide
type safety, validation, and consistent serialization.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Self


@dataclass(frozen=True, slots=True)
class ContentHash:
    """SHA-256 content hash. Immutable, comparable, hashable.

    Canonical string form: ``sha256:<hex-digest>``
    """

    digest: bytes

    def __post_init__(self) -> None:
        if len(self.digest) != 32:
            raise ValueError(f"SHA-256 digest must be 32 bytes, got {len(self.digest)}")

    @classmethod
    def from_data(cls, data: bytes) -> Self:
        """Hash arbitrary data and return a ContentHash."""
        return cls(digest=hashlib.sha256(data).digest())

    @classmethod
    def from_hex(cls, hex_str: str) -> Self:
        """Parse from a bare hex string (64 chars)."""
        return cls(digest=bytes.fromhex(hex_str))

    @classmethod
    def from_prefixed(cls, s: str) -> Self:
        """Parse from canonical ``sha256:<hex>`` form."""
        if not s.startswith("sha256:"):
            raise ValueError(f"Expected 'sha256:' prefix, got: {s!r}")
        return cls.from_hex(s[7:])

    @property
    def hex(self) -> str:
        """Bare hex digest string."""
        return self.digest.hex()

    def __str__(self) -> str:
        return f"sha256:{self.hex}"

    def __repr__(self) -> str:
        return f"ContentHash({self.hex[:16]}...)"

    def __hash__(self) -> int:
        return hash(self.digest)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ContentHash):
            return self.digest == other.digest
        return NotImplemented


@dataclass(frozen=True, slots=True)
class Signature:
    """Ed25519 signature (64 bytes)."""

    raw: bytes

    def __post_init__(self) -> None:
        if len(self.raw) != 64:
            raise ValueError(f"Ed25519 signature must be 64 bytes, got {len(self.raw)}")

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        return cls(raw=data)

    @property
    def hex(self) -> str:
        return self.raw.hex()

    def __str__(self) -> str:
        return self.hex

    def __repr__(self) -> str:
        return f"Signature({self.hex[:16]}...)"

    def __hash__(self) -> int:
        return hash(self.raw)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Signature):
            return self.raw == other.raw
        return NotImplemented


@dataclass(frozen=True, slots=True)
class PublicKey:
    """Ed25519 public key (32 bytes)."""

    raw: bytes

    def __post_init__(self) -> None:
        if len(self.raw) != 32:
            raise ValueError(f"Ed25519 public key must be 32 bytes, got {len(self.raw)}")

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        return cls(raw=data)

    @classmethod
    def from_hex(cls, hex_str: str) -> Self:
        return cls(raw=bytes.fromhex(hex_str))

    @property
    def hex(self) -> str:
        return self.raw.hex()

    @property
    def fingerprint(self) -> str:
        """SHA-256 fingerprint of the public key, truncated to 16 hex chars."""
        return hashlib.sha256(self.raw).hexdigest()[:16]

    def __str__(self) -> str:
        return self.hex

    def __repr__(self) -> str:
        return f"PublicKey({self.fingerprint})"

    def __hash__(self) -> int:
        return hash(self.raw)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PublicKey):
            return self.raw == other.raw
        return NotImplemented


@dataclass(frozen=True, slots=True)
class Timestamp:
    """UTC timestamp with nanosecond precision.

    Stored internally as an integer count of nanoseconds since Unix epoch.
    """

    nanos: int

    @classmethod
    def now(cls) -> Self:
        """Current UTC time."""
        dt = datetime.now(timezone.utc)
        nanos = int(dt.timestamp() * 1_000_000_000)
        return cls(nanos=nanos)

    @classmethod
    def from_datetime(cls, dt: datetime) -> Self:
        """Convert a datetime to a Timestamp. Assumes UTC if naive."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        nanos = int(dt.timestamp() * 1_000_000_000)
        return cls(nanos=nanos)

    @classmethod
    def from_iso(cls, iso_str: str) -> Self:
        """Parse an ISO 8601 string."""
        dt = datetime.fromisoformat(iso_str)
        return cls.from_datetime(dt)

    def to_datetime(self) -> datetime:
        """Convert to a timezone-aware UTC datetime."""
        return datetime.fromtimestamp(self.nanos / 1_000_000_000, tz=timezone.utc)

    def to_iso(self) -> str:
        """ISO 8601 string with microsecond precision (max Python supports)."""
        return self.to_datetime().isoformat()

    def __str__(self) -> str:
        return self.to_iso()

    def __repr__(self) -> str:
        return f"Timestamp({self.to_iso()})"

    def __hash__(self) -> int:
        return hash(self.nanos)

    def __lt__(self, other: Timestamp) -> bool:
        return self.nanos < other.nanos

    def __le__(self, other: Timestamp) -> bool:
        return self.nanos <= other.nanos


@dataclass(frozen=True, slots=True)
class AuditEventId:
    """UUID v7 (time-ordered) identifier for audit events.

    UUID v7 embeds a millisecond timestamp, giving natural chronological
    ordering when sorted lexicographically.
    """

    value: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

    @classmethod
    def generate(cls) -> Self:
        """Generate a new time-ordered UUID v7.

        Falls back to UUID v4 if uuid7 is not available (Python <3.14).
        """
        # Python 3.14+ has uuid.uuid7(); fall back to uuid4 for now.
        try:
            return cls(value=uuid.uuid7())  # type: ignore[attr-defined]
        except AttributeError:
            return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, s: str) -> Self:
        return cls(value=uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"AuditEventId({self.value})"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AuditEventId):
            return self.value == other.value
        return NotImplemented
