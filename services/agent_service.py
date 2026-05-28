import asyncio
import json
import uuid
import time
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from schemas.agent_schema import AgentManifest, AgentStatusResponse, AgentState

app = FastAPI(title="Sovereign Agent API")

# In-memory store for agents (in a real system, this would be etcd or a CRD)
agents_store: Dict[str, dict] = {}
agent_events: Dict[str, list] = {}

async def execute_agent_loop(agent_id: str):
    """
    Lightweight background execution loop.
    In a real implementation, this would invoke the VLLM instance, 
    parse tool calls, and yield SSE events.
    """
    agent = agents_store.get(agent_id)
    if not agent:
        return
        
    policy = agent["manifest"].spec.policy
    
    agent["status"] = "running"
    agent["state"].phase = "executing"
    
    for step in range(1, min(6, policy.max_steps + 1)):
        # Check if paused/deleted
        if agent["status"] != "running":
            break
            
        agent["state"].step = step
        agent_events[agent_id].append({"type": "step_start", "step": step, "timestamp": time.time()})
        
        # Simulate LLM thinking
        await asyncio.sleep(0.5)
        
        # Simulate tool call if tools exist
        tools = agent["manifest"].spec.tools
        if tools and step % 2 != 0:
            tool = tools[0]
            agent["state"].current_tool = tool.name
            agent_events[agent_id].append({"type": "tool_call", "tool": tool.name})
            await asyncio.sleep(0.2)
            agent_events[agent_id].append({"type": "tool_result", "tool": tool.name, "result": "mock_result"})
            agent["state"].current_tool = None
            
        agent_events[agent_id].append({"type": "step_end", "step": step})
        
    if agent["status"] == "running":
        agent["status"] = "completed"
        agent["state"].phase = "done"
        agent_events[agent_id].append({"type": "complete", "result": "Task finished successfully"})


@app.post("/v1/agents", response_model=AgentStatusResponse)
async def submit_agent(manifest: AgentManifest, background_tasks: BackgroundTasks):
    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    
    agents_store[agent_id] = {
        "id": agent_id,
        "name": manifest.metadata.name,
        "manifest": manifest,
        "status": "pending",
        "state": AgentState(total_steps=manifest.spec.policy.max_steps),
        "events_url": f"/v1/agents/{agent_id}/events"
    }
    agent_events[agent_id] = []
    
    background_tasks.add_task(execute_agent_loop, agent_id)
    
    return AgentStatusResponse(
        id=agent_id,
        name=manifest.metadata.name,
        status="pending",
        state=agents_store[agent_id]["state"],
        events_url=agents_store[agent_id]["events_url"]
    )

@app.get("/v1/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str):
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent = agents_store[agent_id]
    return AgentStatusResponse(
        id=agent["id"],
        name=agent["name"],
        status=agent["status"],
        state=agent["state"],
        events_url=agent["events_url"]
    )

@app.post("/v1/agents/{agent_id}/pause")
async def pause_agent(agent_id: str):
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agents_store[agent_id]["status"] == "running":
        agents_store[agent_id]["status"] = "paused"
        agents_store[agent_id]["state"].phase = "paused"
    return {"status": "paused"}

@app.post("/v1/agents/{agent_id}/resume")
async def resume_agent(agent_id: str, background_tasks: BackgroundTasks):
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agents_store[agent_id]["status"] == "paused":
        agents_store[agent_id]["status"] = "running"
        background_tasks.add_task(execute_agent_loop, agent_id)
    return {"status": "running"}

@app.get("/v1/agents/{agent_id}/events")
async def get_agent_events(agent_id: str):
    """In a real implementation this would return a StreamingResponse for SSE"""
    if agent_id not in agents_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"events": agent_events[agent_id]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
