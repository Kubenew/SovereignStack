"""RFC-0007: Event Bus — conformance tests for publish-subscribe."""
import json
import subprocess

BASE = "http://localhost:8546"


def test_event_publish():
    event = {
        "type": "capability.updated",
        "source": "agent://publisher-1",
        "subject": "agent://publisher-1/capability/review",
        "data": {"accuracy": 0.95, "available": True},
        "timestamp": "2026-05-31T12:00:00Z",
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/events/publish",
         "-H", "Content-Type: application/json", "-d", json.dumps(event)],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "published"


def test_event_subscribe():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/events/subscribe",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "subscriber": "agent://subscriber-1",
             "event_types": ["capability.updated", "trust.changed"],
         })],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "subscribed"


def test_event_consume():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/events/consume", "-G",
         "--data-urlencode", "subscriber=agent://subscriber-1",
         "--data-urlencode", "timeout_ms=1000"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    events = json.loads(result.stdout)
    assert isinstance(events, list)


def test_event_ack():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/events/ack",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"subscriber": "agent://subscriber-1", "event_ids": ["evt-1", "evt-2"]})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0


def test_event_unsubscribe():
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{BASE}/events/unsubscribe",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"subscriber": "agent://subscriber-1"})],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0


def test_event_filter_by_type():
    result = subprocess.run(
        ["curl", "-s", f"{BASE}/events/history", "-G",
         "--data-urlencode", "type=capability.updated"],
        capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    events = json.loads(result.stdout)
    assert isinstance(events, list)
