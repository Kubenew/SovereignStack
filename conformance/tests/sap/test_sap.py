"""SAP conformance tests — Sovereign Agent Protocol."""
import json
import subprocess

SAP_ENDPOINT = "http://localhost:8548/sap/v1"


def test_sap_agent_registration():
    agent = {
        "name": "test-agent",
        "public_key": "ed25519:abc123...",
        "capabilities": ["reason", "memory", "knowledge"]
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SAP_ENDPOINT}/agents",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(agent)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "agent_id" in response
    assert "uri" in response
    assert response["uri"].startswith("agent://")


def test_sap_agent_query():
    agent_uri = "agent://test-agent-001"
    query = {"type": "status", "params": {}}
    result = subprocess.run(
        ["curl", "-s", "-X", "POST",
         f"{SAP_ENDPOINT}/agents/{agent_uri}/query",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(query)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "status" in response
    assert "last_active" in response


def test_sap_agent_capabilities():
    agent_uri = "agent://test-agent-001"
    result = subprocess.run(
        ["curl", "-s", f"{SAP_ENDPOINT}/agents/{agent_uri}/capabilities"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert isinstance(response, list)


def test_sap_agent_message():
    msg = {
        "from": "agent://sender-001",
        "to": "agent://receiver-001",
        "type": "request",
        "payload": {"action": "compute", "data": {}}
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SAP_ENDPOINT}/messages",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(msg)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "message_id" in response
    assert "delivered" in response


def test_sap_agent_session_create():
    session = {"agent_uri": "agent://test-agent-001", "ttl_seconds": 300}
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{SAP_ENDPOINT}/sessions",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(session)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "session_id" in response
    assert response["uri"].startswith("session://")


def test_sap_agent_session_terminate():
    session_id = "session://test-session-001"
    result = subprocess.run(
        ["curl", "-s", "-X", "DELETE",
         f"{SAP_ENDPOINT}/sessions/{session_id}"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "terminated"
