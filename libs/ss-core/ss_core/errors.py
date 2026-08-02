"""SovereignStack exception hierarchy.

All exceptions inherit from ``SovereignStackError`` so callers can
catch the entire family with a single except clause.
"""


class SovereignStackError(Exception):
    """Base exception for all SovereignStack errors."""


class UriParseError(SovereignStackError, ValueError):
    """Raised when a SovereignStack URI cannot be parsed."""


class ValidationError(SovereignStackError, ValueError):
    """Raised when data fails validation (wrong length, bad format, etc.)."""


class CryptoError(SovereignStackError):
    """Raised on cryptographic operation failures (bad key, verification fail)."""


class StorageError(SovereignStackError):
    """Raised when the content-addressed store encounters an error."""


class MerkleError(SovereignStackError):
    """Raised when Merkle tree operations fail (bad proof, inconsistency)."""
