# Ollama Adapter for SovereignStack

Bridges Ollama's local inference API into the SovereignStack identity and governance model. Wraps any Ollama model as a SovereignStack capability with UAI identity, provenance logging, and policy enforcement.

## What it does

- Registers Ollama models as SovereignStack capabilities (`capability://ollama/{model}`)
- Logs every inference request to the Merkle audit trail
- Enforces jurisdiction policies (e.g., EU data residency for EU nodes)
- Provides OpenAI-compatible API that SovereignStack agents can call natively
- Reports model lineage via `model://ollama/{model}` URIs

## Quick Start

```bash
# 1. Ensure Ollama is running
ollama serve &

# 2. Pull a model
ollama pull llama3.1

# 3. Start the adapter
python adapter.py --ollama-host http://localhost:11434 --node-url http://localhost:8080

# 4. Test via SovereignStack
curl -X POST http://localhost:9100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "messages": [{"role": "user", "content": "Hello from SovereignStack"}]
  }'
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--ollama-host` | `http://localhost:11434` | Ollama API endpoint |
| `--node-url` | `http://localhost:8080` | SovereignStack node URL |
| `--port` | `9100` | Adapter listen port |
| `--jurisdiction` | `us` | Jurisdiction code for policy enforcement |
| `--audit-log` | `/var/log/sovereignstack/audit.log` | Audit log path |
| `--log-requests` | `true` | Log all inference requests |

## Architecture

```
Ollama Adapter
├── model_registry.py    # Discovers and registers Ollama models
├── inference_proxy.py   # Proxies inference requests with audit logging
├── policy_enforcer.py   # Checks jurisdiction and capability policies
├── adapter.py           # Main entry point (FastAPI server)
└── tests/
    └── test_adapter.py  # Unit tests
```

## Example: Agent calling Ollama via SovereignStack

```python
from sovereign_stack import Agent, Capability

# Agent declares it needs math reasoning
agent = Agent("agent://researcher-1")
agent.require(Capability("capability://ollama/llama3.1"))

# Capability is routed to the Ollama adapter
response = agent.infer("What is 2+2?", capability="capability://ollama/llama3.1")
# Response includes provenance: model://ollama/llama3.1, audit entry in Merkle log
```
