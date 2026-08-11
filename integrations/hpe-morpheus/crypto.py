"""Cryptographic primitives for the SovereignStack x HPE Morpheus integration.

Provides Ed25519 signing/verification when the ``cryptography`` package is
available (recommended) and an HMAC-SHA256 fallback when it is not, so the
demo and conformance suite run on a bare Python install.

Signature mode is exposed via :data:`SIG_ALG` and recorded in evidence metadata
so verifiers know which scheme was used.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

SIG_ALG = "ed25519"
_FALLBACK = False

try:  # pragma: no cover - depends on environment
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
except ImportError:  # pragma: no cover - exercised only without cryptography
    SIG_ALG = "hmac-sha256-fallback"
    _FALLBACK = True


class CryptoError(Exception):
    """Raised when a key or signature is malformed."""


def hash_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def generate_keypair() -> tuple[str, str]:
    """Return ``(private_key_hex, public_key_hex)``.

    Under Ed25519 the private seed is 32 bytes and the public key 32 bytes.
    Under the HMAC fallback the "public key" is the SHA-256 of the private key.
    """
    if _FALLBACK:
        priv = secrets.token_hex(32)
        pub = hash_bytes(bytes.fromhex(priv))
        return priv, pub
    seed = secrets.token_bytes(32)
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return seed.hex(), pub_raw.hex()


def sign(data: bytes, private_key_hex: str) -> str:
    """Sign ``data`` and return the hex-encoded signature."""
    if _FALLBACK:
        key = bytes.fromhex(private_key_hex)
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    try:
        priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
        return priv.sign(data).hex()
    except ValueError as exc:
        raise CryptoError(f"invalid private key: {exc}") from exc


def verify(data: bytes, signature_hex: str, public_key_hex: str) -> bool:
    """Verify a signature. Returns False (never raises) on any failure."""
    try:
        if _FALLBACK:
            key = bytes.fromhex(public_key_hex)
            expected = hmac.new(key, data, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature_hex)
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        pub.verify(bytes.fromhex(signature_hex), data)
        return True
    except Exception:
        return False


def canonical_json(obj) -> bytes:
    """Deterministic canonical JSON bytes (sorted keys, compact separators)."""
    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
