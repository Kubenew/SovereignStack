"""RFC-0002: URI Standard — conformance tests for URI parsing and resolution."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_uri_parse():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/uri/parse", "-G", "--data-urlencode", "uri=agent://researcher-1/capability/review"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["scheme"] == "agent"
    assert parsed["authority"] == "researcher-1"
    assert parsed["path"] == "/capability/review"


def test_uri_scheme_validation():
    schemes = ["agent", "org", "robot", "node", "knowledge", "session", "did", "capability"]
    for scheme in schemes:
        result = subprocess.run(
            ["curl", "-s", f"{BASE}/uri/validate", "-G", "--data-urlencode", f"uri={scheme}://test/value"],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
        assert json.loads(result.stdout)["valid"] is True


def test_uri_invalid_scheme():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/uri/validate", "-G", "--data-urlencode", "uri=invalid://test"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["valid"] is False


def test_uri_query_params():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/uri/parse", "-G", "--data-urlencode",
         "uri=agent://analyst?jurisdiction=EU&language=en"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["query"]["jurisdiction"] == "EU"
    assert parsed["query"]["language"] == "en"


def test_uri_abnf_grammar():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/uri/abnf", "-G", "--data-urlencode",
         "uri=knowledge://org/acme/object/v1.2.3"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    abnf = json.loads(result.stdout)
    assert abnf["abnf"] == uri_grammar()
    assert abnf["matches"] is True


def uri_grammar():
    return "scheme \":\" \"//\" authority path [ \"?\" query ] [ \"#\" fragment ]"


def test_uri_fragment():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/uri/parse", "-G", "--data-urlencode",
         "uri=did:ss:alice#key-1"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["fragment"] == "key-1"
