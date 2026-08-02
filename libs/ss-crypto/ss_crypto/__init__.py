"""ss-crypto: Ed25519 signing, hashing, and signed envelopes for SovereignStack."""

from ss_crypto.keys import KeyPair
from ss_crypto.signing import sign, verify
from ss_crypto.hashing import hash_content, hash_content_hex
from ss_crypto.envelope import SignedEnvelope

__version__ = "0.1.0"

__all__ = [
    "KeyPair",
    "sign",
    "verify",
    "hash_content",
    "hash_content_hex",
    "SignedEnvelope",
]
