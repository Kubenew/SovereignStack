from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ToolParameter(BaseModel):
    type: str
    properties: Dict[str, Any]
    required: Optional[List[str]] = None

class AgentTool(BaseModel):
    type: str = "function"
    name: str
    description: str
    parameters: ToolParameter

class MemoryAttachment(BaseModel):
    source: str
    access: str = "read"

class AgentMemory(BaseModel):
    attach: List[MemoryAttachment] = []

class AgentPolicy(BaseModel):
    sandbox: str = "gvisor"
    allow_network: bool = False
    allow_filesystem_write: bool = False
    max_duration_seconds: int = 300
    max_steps: int = 50
    allowed_tools: List[str] = []

class AgentResources(BaseModel):
    cpu: str = "1"
    memory: str = "1Gi"
    vram_gb: int = 0
    ephemeral_storage: str = "1Gi"

class AgentSpec(BaseModel):
    model: str
    system_prompt: str
    tools: List[AgentTool] = []
    memory: AgentMemory = Field(default_factory=AgentMemory)
    policy: AgentPolicy = Field(default_factory=AgentPolicy)
    resources: AgentResources = Field(default_factory=AgentResources)

class AgentMetadata(BaseModel):
    name: str
    namespace: str = "default"
    labels: Dict[str, str] = {}

class AgentManifest(BaseModel):
    apiVersion: str = "sovereign.ai/v1"
    kind: str = "Agent"
    metadata: AgentMetadata
    spec: AgentSpec

class AgentState(BaseModel):
    phase: str = "pending"
    step: int = 0
    total_steps: int = 50
    current_tool: Optional[str] = None

class AgentStatusResponse(BaseModel):
    id: str
    name: str
    status: str
    state: AgentState
    events_url: str
