"""Ed25519 sign and verify operations.

Stateless functions that operate on raw bytes.
No exceptions on verify failure — returns False.
"""

from __future__ import annotations

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from ss_core.types import Signature, PublicKey


def sign(message: bytes, signing_key: SigningKey) -> Signature:
    """Sign a message with an Ed25519 private key.

    Args:
        message: Arbitrary bytes to sign.
        signing_key: A PyNaCl SigningKey (the private half of a keypair).

    Returns:
        A 64-byte Ed25519 Signature.
    """
    signed = signing_key.sign(message)
    return Signature.from_bytes(signed.signature)


def verify(message: bytes, signature: Signature, public_key: PublicKey) -> bool:
    """Verify an Ed25519 signature against a message and public key.

    Args:
        message: The original message bytes.
        signature: The 64-byte signature to verify.
        public_key: The signer's public key.

    Returns:
        True if the signature is valid, False otherwise.
        Never raises on invalid signatures.
    """
    try:
        vk = VerifyKey(public_key.raw)
        vk.verify(message, signature.raw)
        return True
    except (BadSignatureError, Exception):
        return False
