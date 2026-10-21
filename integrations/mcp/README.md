# SovereignStack MCP Integration

The **Model Context Protocol (MCP)** integration enables AI clients (such as Claude, GPT, Astra, Grok, Qwen, and local open weights) to interact with SovereignStack via an open standard, while keeping SovereignStack in absolute control of authorization, policy enforcement, provenance, and human override.

---

## Architecture Overview

The integration operates in two directions:
1. **MCP Server (`integrations.mcp.server`)**: Exposes SovereignStack's OASA Golden Path (`discover`, `evaluate_action`, `execute_action`, `verify_evidence`) as standard MCP tools, resources, and prompt templates.
2. **Governed MCP Client (`integrations.mcp.client`)**: Wraps third-party MCP servers, routing all external tool invocations through SovereignStack's pre-action authorization gate.

```
AI Clients (Claude, GPT, Local)
       │ (MCP JSON-RPC / SSE)
       ▼
SovereignStack MCP Server (FastMCP)
       │ (OASAService Contract)
       ▼
SovereignStack CoreEngine
       ├── SIRA Policy Engine (Fail-Closed)
       ├── Single-Use Token Store
       └── Target Adapters (Morpheus, K8s, etc.)
```

---

## Installation & Setup

1. Install MCP dependencies:
   ```bash
   pip install "mcp>=1.2.0,<2"
   ```

2. Run the MCP server in standard I/O (stdio) mode:
   ```bash
   python -m integrations.mcp.server
   ```

3. Configure Claude Desktop or MCP Client:
   ```json
   {
     "mcpServers": {
       "sovereignstack": {
         "command": "python",
         "args": ["-m", "integrations.mcp.server"],
         "env": {
           "OASA_MCP_BACKEND": "core",
           "OASA_PRINCIPAL": "agent://claude-infrastructure-assistant"
         }
       }
     }
   }
   ```

---

## Available Tools

| Tool | Description |
| :--- | :--- |
| `get_status` | Gateway and governance status check |
| `discover` | Enumerate available target infrastructure and capabilities |
| `evaluate_action` | Pre-action safety policy evaluation & single-use token issuance |
| `execute_action` | Execute an authorized action via target adapter |
| `get_action` | Fetch cryptographic Action Envelope by ID |
| `get_provenance` | Retrieve immutable execution provenance record |
| `verify_evidence` | Mathematically verify Action Envelope signature and hashes |
| `request_human_approval`| Submit sensitive action for supervisor sign-off |

---

## Security Guarantees

- **Fail-Closed by Default**: Unconfigured or unauthenticated requests cannot perform actions.
- **Anti-Theater**: Denied actions never hit downstream infrastructure.
- **Single-Use Tokens**: Every execution requires an atomic, unexpired token issued by the authorization engine.
- **Independent Verification**: Action envelopes are cryptographically verifiable offline using Ed25519 and `deterministic-json-v1`.
