"""Signed envelope: the atomic unit of trust in SovereignStack.

A SignedEnvelope wraps arbitrary payload bytes with:
- An Ed25519 signature over the payload
- The signer's public key
- A timestamp of when signing occurred
- A SHA-256 content hash of the payload

This is the format used for every audit event stored in the Merkle tree.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Self

from ss_core.types import ContentHash, PublicKey, Signature, Timestamp
from ss_crypto.hashing import hash_content
from ss_crypto.keys import KeyPair
from ss_crypto.signing import sign, verify


@dataclass(frozen=True, slots=True)
class SignedEnvelope:
    """A signed, tamper-evident container for arbitrary data.

    Attributes:
        payload: The raw payload bytes.
        signature: Ed25519 signature over the payload.
        public_key: The signer's public key.
        signed_at: UTC timestamp of signing.
        content_hash: SHA-256 hash of the payload.
    """

    payload: bytes
    signature: Signature
    public_key: PublicKey
    signed_at: Timestamp
    content_hash: ContentHash

    @classmethod
    def create(cls, payload: bytes, keypair: KeyPair) -> Self:
        """Sign a payload and wrap it in an envelope.

        Args:
            payload: Arbitrary bytes to sign (typically JSON-encoded audit event).
            keypair: The Ed25519 keypair to sign with.

        Returns:
            A new, verified SignedEnvelope.
        """
        timestamp = Timestamp.now()
        content_hash = hash_content(payload)
        sig = sign(payload, keypair._signing_key)

        return cls(
            payload=payload,
            signature=sig,
            public_key=keypair.public_key,
            signed_at=timestamp,
            content_hash=content_hash,
        )

    def verify_signature(self) -> bool:
        """Verify that the envelope's signature is valid for the payload."""
        return verify(self.payload, self.signature, self.public_key)

    def verify_hash(self) -> bool:
        """Verify that the content hash matches the payload."""
        return hash_content(self.payload) == self.content_hash

    def verify_all(self) -> bool:
        """Verify both signature and content hash."""
        return self.verify_signature() and self.verify_hash()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary.

        Payload and binary fields are base64-encoded for safe transport.
        """
        return {
            "payload": base64.b64encode(self.payload).decode("ascii"),
            "signature": base64.b64encode(self.signature.raw).decode("ascii"),
            "public_key": base64.b64encode(self.public_key.raw).decode("ascii"),
            "signed_at": self.signed_at.to_iso(),
            "content_hash": str(self.content_hash),
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from a dictionary (e.g., parsed JSON)."""
        payload = base64.b64decode(data["payload"])
        signature = Signature.from_bytes(base64.b64decode(data["signature"]))
        public_key = PublicKey.from_bytes(base64.b64decode(data["public_key"]))
        signed_at = Timestamp.from_iso(data["signed_at"])
        content_hash = ContentHash.from_prefixed(data["content_hash"])

        return cls(
            payload=payload,
            signature=signature,
            public_key=public_key,
            signed_at=signed_at,
            content_hash=content_hash,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Deserialize from a JSON string."""
        return cls.from_dict(json.loads(json_str))
