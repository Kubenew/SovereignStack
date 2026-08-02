"""Tests for ss-crypto: keys, signing, hashing, and envelopes."""

import json
import tempfile
from pathlib import Path

import pytest

from ss_core.types import ContentHash, Signature, PublicKey
from ss_crypto.keys import KeyPair
from ss_crypto.signing import sign, verify
from ss_crypto.hashing import hash_content, hash_content_hex, hash_concat
from ss_crypto.envelope import SignedEnvelope


class TestHashing:
    def test_hash_content_returns_content_hash(self):
        h = hash_content(b"hello")
        assert isinstance(h, ContentHash)
        assert len(h.digest) == 32

    def test_hash_content_deterministic(self):
        h1 = hash_content(b"test")
        h2 = hash_content(b"test")
        assert h1 == h2

    def test_hash_content_hex(self):
        h = hash_content_hex(b"test")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_hash_concat(self):
        h1 = hash_concat(b"a", b"b")
        h2 = hash_content(b"ab")
        assert h1 == h2

    def test_different_inputs_different_hashes(self):
        h1 = hash_content(b"a")
        h2 = hash_content(b"b")
        assert h1 != h2


class TestKeyPair:
    def test_generate(self):
        kp = KeyPair.generate()
        assert isinstance(kp.public_key, PublicKey)
        assert len(kp.public_key.raw) == 32

    def test_from_seed_deterministic(self):
        seed = b"\x42" * 32
        kp1 = KeyPair.from_seed(seed)
        kp2 = KeyPair.from_seed(seed)
        assert kp1.public_key == kp2.public_key

    def test_from_seed_invalid_length(self):
        with pytest.raises(Exception, match="32 bytes"):
            KeyPair.from_seed(b"short")

    def test_save_and_load(self):
        kp = KeyPair.generate()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "keypair.json"
            kp.save(path)

            loaded = KeyPair.load(path)
            assert loaded.public_key == kp.public_key

    def test_save_format(self):
        kp = KeyPair.generate()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "keypair.json"
            kp.save(path)

            data = json.loads(path.read_text())
            assert data["format"] == "sovereignstack-keypair-v1"
            assert "private_key_hex" in data
            assert "public_key_hex" in data

    def test_private_bytes_roundtrip(self):
        kp = KeyPair.generate()
        raw = kp.private_bytes()
        kp2 = KeyPair.from_private_bytes(raw)
        assert kp.public_key == kp2.public_key

    def test_str_does_not_leak_private_key(self):
        kp = KeyPair.generate()
        s = str(kp)
        assert "private" not in s.lower()
        assert kp.public_key.fingerprint in s


class TestSigning:
    def test_sign_and_verify(self):
        kp = KeyPair.generate()
        message = b"hello world"
        sig = sign(message, kp._signing_key)
        assert isinstance(sig, Signature)
        assert verify(message, sig, kp.public_key)

    def test_verify_wrong_message(self):
        kp = KeyPair.generate()
        sig = sign(b"original", kp._signing_key)
        assert not verify(b"tampered", sig, kp.public_key)

    def test_verify_wrong_key(self):
        kp1 = KeyPair.generate()
        kp2 = KeyPair.generate()
        sig = sign(b"message", kp1._signing_key)
        assert not verify(b"message", sig, kp2.public_key)

    def test_verify_returns_false_not_exception(self):
        kp = KeyPair.generate()
        sig = sign(b"ok", kp._signing_key)
        # Corrupt the signature
        bad_sig = Signature.from_bytes(b"\x00" * 64)
        result = verify(b"ok", bad_sig, kp.public_key)
        assert result is False


class TestSignedEnvelope:
    def test_create_and_verify(self):
        kp = KeyPair.generate()
        payload = b'{"event": "test"}'
        env = SignedEnvelope.create(payload, kp)

        assert env.payload == payload
        assert env.verify_signature()
        assert env.verify_hash()
        assert env.verify_all()

    def test_json_roundtrip(self):
        kp = KeyPair.generate()
        env = SignedEnvelope.create(b"test payload", kp)

        json_str = env.to_json()
        env2 = SignedEnvelope.from_json(json_str)

        assert env2.payload == env.payload
        assert env2.signature == env.signature
        assert env2.public_key == env.public_key
        assert env2.content_hash == env.content_hash
        assert env2.verify_all()

    def test_dict_roundtrip(self):
        kp = KeyPair.generate()
        env = SignedEnvelope.create(b"data", kp)

        d = env.to_dict()
        env2 = SignedEnvelope.from_dict(d)

        assert env2.payload == env.payload
        assert env2.verify_all()

    def test_tampered_payload_fails_verify(self):
        kp = KeyPair.generate()
        env = SignedEnvelope.create(b"original", kp)

        # Manually tamper with the payload
        tampered = SignedEnvelope(
            payload=b"tampered",
            signature=env.signature,
            public_key=env.public_key,
            signed_at=env.signed_at,
            content_hash=env.content_hash,
        )
        assert not tampered.verify_signature()
        assert not tampered.verify_hash()
        assert not tampered.verify_all()

    def test_json_output_structure(self):
        kp = KeyPair.generate()
        env = SignedEnvelope.create(b"test", kp)

        d = env.to_dict()
        assert "payload" in d
        assert "signature" in d
        assert "public_key" in d
        assert "signed_at" in d
        assert "content_hash" in d
        assert d["content_hash"].startswith("sha256:")
