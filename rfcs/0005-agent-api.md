# RFC 0005: Agent API Specification

| Field | Value |
|---|---|
| **Status** | Draft |
| **Author** | SovereignStack Core Team |
| **Created** | 2026-05-27 |
| **Category** | Standards Track |

---

## Summary

Define the Sovereign Agent API — the interface for submitting, managing, and interacting with AI agents on a sovereign node. Agents are long-running, stateful, sandboxed workloads that combine model inference with tool execution, memory access, and policy enforcement. The API follows Kubernetes-style declarative manifests with an async execution model.

---

## Motivation

As the project evolves from single-shot chat completions to autonomous agent workflows, a standard agent API is needed. Without it:

- Each agent framework (LangChain, CrewAI, AutoGen) uses its own API shape
- No consistent way to attach sovereign memory or apply policy
- No standard sandboxing or resource isolation for agents
- Audit attribution across multi-step agent actions is ad-hoc

A standard Agent API enables the entire project to treat agents as first-class primitives alongside inference and memory.

---

## Design

### API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/v1/agents` | POST | Submit a new agent |
| `/v1/agents` | GET | List agents |
| `/v1/agents/{id}` | GET | Get agent status |
| `/v1/agents/{id}` | DELETE | Stop and remove agent |
| `/v1/agents/{id}/pause` | POST | Pause agent execution |
| `/v1/agents/{id}/resume` | POST | Resume paused agent |
| `/v1/agents/{id}/events` | GET | Stream agent events (SSE) |
| `/v1/agents/{id}/result` | GET | Get final result |

### Agent Manifest

```yaml
apiVersion: sovereign.ai/v1
kind: Agent
metadata:
  name: document-analyzer
  namespace: default
  labels:
    risk-tier: "standard"
spec:
  model: "sovereign-llama3"
  system_prompt: |
    You are a document analysis agent. Use the tools below to answer
    questions about uploaded documents.
  tools:
    - type: function
      name: search_documents
      description: Search uploaded documents
      parameters:
        type: object
        properties:
          query:
            type: string
          max_results:
            type: integer
            default: 5
    - type: function
      name: summarize
      description: Summarize a document
      parameters:
        type: object
        properties:
          doc_id:
            type: string
  memory:
    attach:
      - source: "vector:corpus-v1"
        access: "read"
      - source: "kv:session-cache"
        access: "read-write"
  policy:
    sandbox: "gvisor"
    allow_network: false
    allow_filesystem_write: false
    max_duration_seconds: 300
    max_steps: 50
    allowed_tools: ["search_documents", "summarize"]
  resources:
    cpu: "2"
    memory: "2Gi"
    vram_gb: 4
    ephemeral_storage: "1Gi"
  schedule:
    replicas: 1
    restart: "on-failure"
    max_retries: 3
```

### Agent Status

```json
{
  "id": "agent-9f7a2b1c",
  "name": "document-analyzer",
  "status": "running",
  "state": {
    "phase": "executing",
    "step": 4,
    "total_steps": 50,
    "current_tool": "search_documents"
  },
  "resources": {
    "cpu_usage": "0.45",
    "memory_usage_mb": 512,
    "vram_usage_gb": 2.1
  },
  "timeline": {
    "submitted": "2026-05-27T09:00:00Z",
    "started": "2026-05-27T09:00:02Z",
    "estimated_end": "2026-05-27T09:05:00Z"
  },
  "events_url": "/v1/agents/agent-9f7a2b1c/events"
}
```

### Event Stream (SSE)

```
data: {"type":"step_start","step":1,"tool":"search_documents","timestamp":"..."}
data: {"type":"tool_call","tool":"search_documents","args":{"query":"annual report"},"duration_ms":1200}
data: {"type":"tool_result","tool":"search_documents","result_summary":"Found 3 documents"}
data: {"type":"step_end","step":1,"duration_ms":1500}
data: {"type":"inference","tokens_prompt":42,"tokens_completion":156}
data: {"type":"complete","result_summary":"Analysis complete"}
```

### Agent Lifecycle

```
                     ┌──────────────┐
                     │   SUBMITTED  │
                     └──────┬───────┘
                            │ validation
                     ┌──────▼───────┐
                     │   PENDING    │
                     └──────┬───────┘
                            │ scheduled
                     ┌──────▼───────┐
            ┌────────┤   RUNNING    │
            │        └──────┬───────┘
            │               │
     ┌──────▼───────┐  ┌───▼─────────┐
     │   PAUSED     │  │  COMPLETED  │
     └──────┬───────┘  └──────┬──────┘
            │                  │
     ┌──────▼───────┐  ┌──────▼───────┐
     │   RESUMED    │  │   ARCHIVED   │
     └──────┬───────┘  └──────────────┘
            │
     ┌──────▼───────┐
     │   FAILED     │
     └──────────────┘
```

### Tool Execution

Tools are registered via a plugin interface:

```python
@agent_tool(
    name="search_documents",
    description="Search uploaded documents by query",
    parameters={
        "query": {"type": "string"},
        "max_results": {"type": "integer", "default": 5}
    }
)
async def search_documents(query: str, max_results: int = 5) -> list[dict]:
    # Tool code runs inside the agent sandbox
    results = await memory_service.search(query, top_k=max_results)
    return [{"doc_id": r.id, "snippet": r.snippet} for r in results]
```

Each tool call is:
- Audited to the event log with parameters and result summary
- Subject to policy (`allowed_tools`, rate limits)
- Timeout-protected (default 30s per call)

### Memory Attachment

Memory is attached before agent start and detached on completion:

| Attachment Mode | Behavior |
|---|---|
| `read` | Vector store queries allowed, writes blocked |
| `read-write` | Full read/write access to the attached store |
| `append` | Append-only (for event log attachment) |

### Resource Enforcement

| Resource | Enforcement |
|---|---|
| CPU | cgroup `cpu.max` |
| Memory | cgroup `memory.max` |
| VRAM | GPU memory allocation via CUDA_VISIBLE_DEVICES + vLLM slot |
| Ephemeral storage | tmpfs size limit |
| Duration | Kill after `max_duration_seconds` (SIGTERM → SIGKILL) |
| Steps | Kill after `max_steps` tool calls |

---

## Security Considerations

| Threat | Mitigation |
|---|---|
| Tool abuse | `allowed_tools` whitelist, rate-limited |
| Memory exfiltration | Read-only attachment when possible |
| Escalation | gVisor sandbox, no host network/filesystem |
| Data leakage across agents | Per-agent memory isolation, no shared tmpfs |
| Model prompt injection | System prompt prefix enforced, output filtering (planned) |

---

## Compatibility

- Backward compatible: existing `/v1/chat/completions` continues to work
- Agent API is additive — does not change existing endpoints
- Tool plugins are Python-native; future RFCs may define WASM-based plugins

---

## Deployment Strategy

| Phase | Scope |
|---|---|
| Phase 1 | Agent submit/get/list/delete, single step, no tools |
| Phase 2 | Tool execution, memory attachment, event streaming |
| Phase 3 | Scheduling, resource enforcement, pause/resume |
| Phase 4 | Multi-agent coordination, agent-to-agent messaging |

---

## Migration Path

Existing chat completions can be wrapped as single-step agents:

```python
# Before
response = client.chat.completions.create(model="...", messages=[...])

# After
agent = client.agents.create(
    manifest={
        "model": "...",
        "tools": [],
        "system_prompt": messages[0]["content"] if messages else "",
    }
)
result = client.agents.result(agent.id)
```

---

## Alternatives Considered

| Alternative | Reason Not Selected |
|---|---|
| LangChain Remote Runtime | Vendor lock-in, no sovereignty guarantees |
| Custom agent protocol | Too bespoke; OpenAI Assistants API pattern is familiar |
| No agent abstraction | Cannot support autonomous workflows |
| WASM-only tools | WASM ecosystem immature; Python plugins first |

---

## References

- [OpenAI Assistants API](https://platform.openai.com/docs/api-reference/assistants)
- [LangChain Agent Protocol](https://python.langchain.com)
- [Kubernetes Pod Spec](https://kubernetes.io/docs/concepts/workloads/pods/)
