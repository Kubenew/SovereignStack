"""SIP conformance tests — Sovereign Intelligence Protocol."""
import json
import subprocess

SIP_ENDPOINT = "http://localhost:8546/sip/v1"


def test_sip_handshake():
    result = subprocess.run(
        ["curl", "-s", f"{SIP_ENDPOINT}/handshake"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "node_id" in response
    assert "protocol_version" in response
    assert response["protocol_version"] >= "1.0"


def test_sip_ping():
    result = subprocess.run(
        ["curl", "-s", f"{SIP_ENDPOINT}/ping"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "pong"


def test_sip_capability_exchange():
    payload = json.dumps({"capabilities": ["resolve", "query", "subscribe"]})
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SIP_ENDPOINT}/capabilities",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "matched" in response
    assert "peer_capabilities" in response


def test_sip_message_roundtrip():
    message = {"type": "request", "payload": {"query": "test"}}
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SIP_ENDPOINT}/message",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(message)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["type"] == "response"
    assert "payload" in response


def test_sip_error_handling():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SIP_ENDPOINT}/message",
         "-H", "Content-Type: application/json", "-d", "invalid"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "error" in response
    assert response["error"]["code"] >= 400
