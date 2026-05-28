import json
import pytest
from fastapi.testclient import TestClient

from services.agent_service import app as agent_app
from services.federation_service import app as federation_app
from services.marketplace_service import app as marketplace_app

agent_client = TestClient(agent_app)
federation_client = TestClient(federation_app)
marketplace_client = TestClient(marketplace_app)

def test_agent_lifecycle():
    # 1. Submit an agent
    manifest = {
        "apiVersion": "sovereign.ai/v1",
        "kind": "Agent",
        "metadata": {
            "name": "test-analyser"
        },
        "spec": {
            "model": "sovereign-test",
            "system_prompt": "You are a test agent",
            "policy": {
                "max_steps": 2
            }
        }
    }
    
    resp = agent_client.post("/v1/agents", json=manifest)
    assert resp.status_code == 200
    data = resp.json()
    agent_id = data["id"]
    assert data["status"] == "pending"
    
    # Let the background task spin up (mocked via fast async loop)
    import time
    time.sleep(1) 
    
    # 2. Check status
    resp = agent_client.get(f"/v1/agents/{agent_id}")
    data = resp.json()
    assert data["status"] in ["running", "completed"]
    
    # 3. Check events
    resp = agent_client.get(f"/v1/agents/{agent_id}/events")
    events = resp.json()["events"]
    assert len(events) > 0
    assert events[0]["type"] == "step_start"

def test_federated_agent_message():
    # Target our local node
    msg = {
        "source_agent_id": "agent-123",
        "target_agent_id": "agent-456",
        "target_node_id": "mock-node-id", # Will fail local delivery check since we didn't set NODE_ID env var in test exactly
        "payload": {"hello": "world"}
    }
    
    # Test unauthorized
    resp = federation_client.post("/mesh/agent/message", json=msg)
    assert resp.status_code == 401
    
    # Test authorized but routing failure (mock-node-id not in mesh)
    resp = federation_client.post(
        "/mesh/agent/message", 
        json=msg,
        headers={"Authorization": "Bearer default-federation-token"}
    )
    # Target node not found because we didn't mock a peer
    assert resp.status_code == 404

def test_marketplace_publishing():
    metadata = {
        "bundle_id": "sovereign/test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "author": "sovereign",
        "type": "tool-plugin",
        "description": "A test plugin"
    }
    
    resp = marketplace_client.post(
        "/v1/marketplace/publish",
        data={"metadata": json.dumps(metadata)}
        # Omitting payload for simple test
    )
    
    if resp.status_code == 409:
        # Already exists from previous test run
        pass
    else:
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"
        
    # Search for it
    resp = marketplace_client.get("/v1/marketplace/search?query=test")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    assert any(r["bundle_id"] == "sovereign/test-plugin" for r in results)
