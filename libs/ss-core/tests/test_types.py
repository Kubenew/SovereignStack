"""Tests for ss_core.types."""

import pytest
from ss_core.types import ContentHash, Signature, PublicKey, Timestamp, AuditEventId
from datetime import datetime, timezone


class TestContentHash:
    def test_from_data(self):
        h = ContentHash.from_data(b"hello world")
        assert len(h.digest) == 32
        assert h.hex == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_from_hex_roundtrip(self):
        h1 = ContentHash.from_data(b"test")
        h2 = ContentHash.from_hex(h1.hex)
        assert h1 == h2

    def test_from_prefixed(self):
        h = ContentHash.from_data(b"test")
        h2 = ContentHash.from_prefixed(str(h))
        assert h == h2

    def test_str_has_prefix(self):
        h = ContentHash.from_data(b"x")
        assert str(h).startswith("sha256:")

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match="32 bytes"):
            ContentHash(digest=b"short")

    def test_hashable(self):
        h1 = ContentHash.from_data(b"a")
        h2 = ContentHash.from_data(b"a")
        assert {h1, h2} == {h1}

    def test_different_data_different_hash(self):
        h1 = ContentHash.from_data(b"a")
        h2 = ContentHash.from_data(b"b")
        assert h1 != h2


class TestSignature:
    def test_valid_64_bytes(self):
        sig = Signature.from_bytes(b"\x00" * 64)
        assert len(sig.raw) == 64

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match="64 bytes"):
            Signature(raw=b"short")

    def test_hex_roundtrip(self):
        sig = Signature.from_bytes(b"\xab" * 64)
        assert len(sig.hex) == 128


class TestPublicKey:
    def test_valid_32_bytes(self):
        pk = PublicKey.from_bytes(b"\x01" * 32)
        assert len(pk.raw) == 32

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match="32 bytes"):
            PublicKey(raw=b"short")

    def test_fingerprint(self):
        pk = PublicKey.from_bytes(b"\x01" * 32)
        assert len(pk.fingerprint) == 16

    def test_from_hex(self):
        pk = PublicKey.from_bytes(b"\xab" * 32)
        pk2 = PublicKey.from_hex(pk.hex)
        assert pk == pk2


class TestTimestamp:
    def test_now(self):
        ts = Timestamp.now()
        assert ts.nanos > 0

    def test_from_datetime(self):
        dt = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)
        ts = Timestamp.from_datetime(dt)
        roundtrip = ts.to_datetime()
        assert roundtrip.year == 2026
        assert roundtrip.month == 7
        assert roundtrip.day == 31

    def test_from_iso(self):
        ts = Timestamp.from_iso("2026-07-31T12:00:00+00:00")
        dt = ts.to_datetime()
        assert dt.year == 2026

    def test_ordering(self):
        t1 = Timestamp(nanos=1000)
        t2 = Timestamp(nanos=2000)
        assert t1 < t2
        assert t1 <= t2
        assert not t2 < t1

    def test_iso_roundtrip(self):
        ts = Timestamp.now()
        iso = ts.to_iso()
        ts2 = Timestamp.from_iso(iso)
        # Microsecond precision means we may lose sub-microsecond nanos
        assert abs(ts.nanos - ts2.nanos) < 1000


class TestAuditEventId:
    def test_generate(self):
        eid = AuditEventId.generate()
        assert eid.value is not None

    def test_from_string_roundtrip(self):
        eid = AuditEventId.generate()
        eid2 = AuditEventId.from_string(str(eid))
        assert eid == eid2

    def test_uniqueness(self):
        ids = {AuditEventId.generate() for _ in range(100)}
        assert len(ids) == 100
