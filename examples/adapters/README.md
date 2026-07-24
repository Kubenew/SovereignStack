# SovereignStack Inference Adapters

Adapters bridge external inference providers into the SovereignStack identity and governance model. Each adapter wraps a provider's API as a SovereignStack capability with UAI identity, provenance logging, and policy enforcement.

## Available Adapters

| Adapter | Provider | Port | Description |
|---------|----------|------|-------------|
| [Ollama](ollama/) | Ollama (local) | 9100 | Local inference with Ollama models |
| [vLLM](vllm/) | vLLM (GPU cluster) | 9200 | High-throughput GPU inference |

## What adapters provide

- **Capability registration**: Models become `capability://ollama/{model}` or `capability://vllm/{model}`
- **Audit logging**: Every inference request logged to Merkle audit trail
- **Policy enforcement**: Jurisdiction-based access control before inference
- **Provenance tracking**: `model://` URIs for every model used
- **OpenAI-compatible API**: Standard `/v1/chat/completions` endpoint

## Quick Start

```bash
# Ollama adapter
cd examples/adapters/ollama
pip install -r requirements.txt
python adapter.py --ollama-host http://localhost:11434

# vLLM adapter
cd examples/adapters/vllm
pip install -r requirements.txt
python adapter.py --vllm-host http://localhost:8000
```

## Using with SovereignStack agents

```python
from sovereign_stack import Agent, Capability

agent = Agent("agent://my-agent")
agent.require(Capability("capability://ollama/llama3.1"))
response = agent.infer("Hello", capability="capability://ollama/llama3.1")
```

## Adding a new adapter

1. Create `examples/adapters/{provider}/`
2. Implement OpenAI-compatible proxy with audit logging
3. Register models as `capability://` and `model://` URIs
4. Add tests in `tests/`
5. Update this README
