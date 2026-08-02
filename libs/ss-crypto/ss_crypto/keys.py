"""Ed25519 keypair management.

Uses PyNaCl (libsodium bindings) for all cryptographic operations.
Keys are serialized in raw 32/64-byte format for storage and in
hex-encoded form for display/config.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from nacl.signing import SigningKey, VerifyKey

from ss_core.errors import CryptoError
from ss_core.types import PublicKey


@dataclass(frozen=True)
class KeyPair:
    """An Ed25519 signing keypair.

    The ``_signing_key`` is the private half (seed + public key, 64 bytes).
    The ``public_key`` is the public half (32 bytes), exposed as an ss-core type.
    """

    _signing_key: SigningKey
    public_key: PublicKey

    @classmethod
    def generate(cls) -> Self:
        """Generate a fresh random Ed25519 keypair."""
        sk = SigningKey.generate()
        pk = PublicKey.from_bytes(bytes(sk.verify_key))
        return cls(_signing_key=sk, public_key=pk)

    @classmethod
    def from_seed(cls, seed: bytes) -> Self:
        """Create a keypair deterministically from a 32-byte seed.

        This is useful for testing and for deriving keys from a master secret.
        """
        if len(seed) != 32:
            raise CryptoError(f"Seed must be 32 bytes, got {len(seed)}")
        sk = SigningKey(seed)
        pk = PublicKey.from_bytes(bytes(sk.verify_key))
        return cls(_signing_key=sk, public_key=pk)

    @classmethod
    def from_private_bytes(cls, private_bytes: bytes) -> Self:
        """Load from raw 32-byte private key (seed)."""
        return cls.from_seed(private_bytes)

    def private_bytes(self) -> bytes:
        """Return the raw 32-byte private key (seed).

        Handle with extreme care — this is the secret.
        """
        return bytes(self._signing_key)

    def save(self, path: Path | str) -> None:
        """Save the keypair to a JSON file.

        The file contains both the private seed (hex) and the public key (hex).
        The file should be protected with appropriate filesystem permissions.
        """
        path = Path(path)
        data = {
            "format": "sovereignstack-keypair-v1",
            "private_key_hex": bytes(self._signing_key).hex(),
            "public_key_hex": self.public_key.hex,
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path | str) -> Self:
        """Load a keypair from a JSON file created by ``save()``."""
        path = Path(path)
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise CryptoError(f"Failed to load keypair from {path}: {e}") from e

        if data.get("format") != "sovereignstack-keypair-v1":
            raise CryptoError(f"Unknown keypair format: {data.get('format')}")

        seed = bytes.fromhex(data["private_key_hex"])
        return cls.from_seed(seed)

    @property
    def verify_key(self) -> VerifyKey:
        """The PyNaCl VerifyKey for signature verification."""
        return self._signing_key.verify_key

    def __repr__(self) -> str:
        return f"KeyPair(public_key={self.public_key!r})"

    # Prevent accidental leaking of private key in logs/debugger
    def __str__(self) -> str:
        return f"KeyPair(pubkey={self.public_key.fingerprint})"
