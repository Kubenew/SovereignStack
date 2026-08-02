"""Tests for ss_core.uri."""

import pytest
from ss_core.uri import SsUri, parse_uri
from ss_core.errors import UriParseError


class TestSsUri:
    def test_parse_valid(self):
        uri = SsUri.parse("ss://acme.corp/audit/evt-001")
        assert uri.authority == "acme.corp"
        assert uri.resource_type == "audit"
        assert uri.resource_id == "evt-001"

    def test_parse_with_colons_in_id(self):
        uri = SsUri.parse("ss://localhost/cas/sha256:abcdef1234")
        assert uri.resource_id == "sha256:abcdef1234"

    def test_roundtrip(self):
        original = "ss://globex.inc/key/ed25519-abc123"
        uri = SsUri.parse(original)
        assert str(uri) == original

    def test_wrong_scheme_raises(self):
        with pytest.raises(UriParseError, match="must start with"):
            SsUri.parse("http://acme.corp/audit/evt-001")

    def test_too_few_segments_raises(self):
        with pytest.raises(UriParseError, match="3 path segments"):
            SsUri.parse("ss://acme.corp/audit")

    def test_too_many_segments_raises(self):
        with pytest.raises(UriParseError, match="3 path segments"):
            SsUri.parse("ss://acme.corp/audit/sub/evt-001")

    def test_empty_authority_raises(self):
        with pytest.raises(UriParseError):
            SsUri.parse("ss:///audit/evt-001")

    def test_invalid_resource_type_uppercase(self):
        with pytest.raises(UriParseError, match="resource_type"):
            SsUri.parse("ss://acme.corp/AUDIT/evt-001")

    def test_invalid_authority_starts_with_hyphen(self):
        with pytest.raises(UriParseError, match="authority"):
            SsUri.parse("ss://-acme/audit/evt-001")

    def test_constructor_validates(self):
        # Direct construction also validates
        with pytest.raises(UriParseError):
            SsUri(authority="", resource_type="audit", resource_id="x")

    def test_frozen(self):
        uri = SsUri.parse("ss://acme.corp/audit/evt-001")
        with pytest.raises(AttributeError):
            uri.authority = "other"  # type: ignore[misc]

    def test_equality(self):
        u1 = SsUri.parse("ss://a.b/c/d")
        u2 = SsUri.parse("ss://a.b/c/d")
        assert u1 == u2

    def test_parse_uri_convenience(self):
        uri = parse_uri("ss://a.b/c/d")
        assert uri.authority == "a.b"
