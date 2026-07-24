# vLLM Adapter for SovereignStack

Bridges vLLM's high-throughput inference server into the SovereignStack identity and governance model. Designed for production GPU clusters running frontier models.

## What it does

- Registers vLLM-served models as SovereignStack capabilities (`capability://vllm/{model}`)
- Logs every inference request to the Merkle audit trail with full provenance
- Enforces jurisdiction policies and capability-based access control
- Provides OpenAI-compatible API with SovereignStack metadata
- Reports model lineage via `model://vllm/{model}` URIs
- Supports structured output, function calling, and streaming

## Quick Start

```bash
# 1. Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-70B \
  --port 8000 \
  --tensor-parallel-size 4

# 2. Start the adapter
python adapter.py --vllm-host http://localhost:8000 --node-url http://localhost:8080

# 3. Test via SovereignStack
curl -X POST http://localhost:9200/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-70B",
    "messages": [{"role": "user", "content": "Analyze this contract for compliance risks"}]
  }'
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--vllm-host` | `http://localhost:8000` | vLLM API endpoint |
| `--node-url` | `http://localhost:8080` | SovereignStack node URL |
| `--port` | `9200` | Adapter listen port |
| `--jurisdiction` | `us` | Jurisdiction code for policy enforcement |
| `--audit-log` | `/var/log/sovereignstack/audit.log` | Audit log path |
| `--max-tokens` | `4096` | Default max tokens |
| `--enforce-usage` | `true` | Require usage reporting in audit |

## Architecture

```
vLLM Adapter
├── model_registry.py    # Discovers and registers vLLM models
├── inference_proxy.py   # Proxies with audit + provenance logging
├── policy_enforcer.py   # Jurisdiction + capability enforcement
├── usage_tracker.py     # Token usage accounting per agent
├── adapter.py           # Main entry point (FastAPI server)
└── tests/
    └── test_adapter.py  # Unit tests
```

## Example: Frontier model with provenance

```python
from sovereign_stack import Agent, Capability, Provenance

agent = Agent("agent://compliance-reviewer")
agent.require(Capability("capability://vllm/meta-llama/Llama-3.1-70B"))

# Inference with full provenance
response = agent.infer(
    "Review this loan application for fair lending compliance",
    capability="capability://vllm/meta-llama/Llama-3.1-70B",
)

# Provenance chain:
# model://vllm/meta-llama/Llama-3.1-70B
# reasoning://compliance-review/{session}
# audit://merkle/{entry}
```
