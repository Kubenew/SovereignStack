"""RFC-0009: Session Lifecycle — conformance tests for session management."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_session_create():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/sessions/create",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "agent": "agent://researcher-1",
             "capabilities": ["knowledge_query", "reasoning"],
             "ttl_secs": 3600,
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    session = json.loads(result.stdout)
    assert "session_id" in session
    assert session["status"] == "active"


def test_session_heartbeat():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/sessions/heartbeat",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"session_id": "session-1"})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "extended"


def test_session_query():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/sessions/session-1/status"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    session = json.loads(result.stdout)
    assert "status" in session


def test_session_expire():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/sessions/expire",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"session_id": "session-1"})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "expired"


def test_session_list_active():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/sessions/active"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    sessions = json.loads(result.stdout)
    assert isinstance(sessions, list)


def test_session_history():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/sessions/history", "-G",
         "--data-urlencode", "agent=agent://researcher-1",
         "--data-urlencode", "limit=10"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    history = json.loads(result.stdout)
    assert isinstance(history, list)
