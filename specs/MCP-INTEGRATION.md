# SovereignStack MCP Integration Specification

**Standard Identifier**: `OASA-EXT-MCP-0.1`  
**Status**: NORMATIVE EXTENSION  
**Target Architecture**: Open Autonomous System Architecture (OASA) v0.6  
**Reference Implementations**: `integrations/mcp`

---

## 1. Architectural Principles

The Model Context Protocol (MCP) provides an open standard for AI models to discover and invoke tools, read context resources, and access approved workflow prompts.

In SovereignStack, **MCP acts purely as an interoperability transport layer**. SovereignStack's core governance engine retains sole authority over:
1. **Identity & Principal Binding**: Requests are attributed to cryptographically authenticated principals, not self-reported model strings.
2. **Pre-Action Policy Authorization (SIRA)**: Tools and actions are evaluated before any downstream API call is made.
3. **Single-Use Atomic Leases**: Successful evaluations produce single-use, bounded-lifetime authorization tokens.
4. **Anti-Theater Invariant**: Denied actions produce verifiable denial records with **zero** downstream provider execution.
5. **Cryptographic Provenance**: Executions produce Ed25519-signed Action Envelopes using canonical `deterministic-json-v1`.

```
+-------------------------------------------------------------+
|               AI Clients & Autonomous Agents                |
|           (Claude, GPT, Astra, Grok, Qwen, Local)           |
+-------------------------------------------------------------+
                              |
                              | MCP (JSON-RPC 2.0 / SSE)
                              v
+-------------------------------------------------------------+
|             SovereignStack MCP Gateway                      |
|  Tools (Governed) | Resources (Context) | Prompts (Workflows)|
+-------------------------------------------------------------+
                              |
                     OASAService Contract
                              |
                              v
+-------------------------------------------------------------+
|              SovereignStack OASA Core Engine                |
|  [DISCOVER] -> [AUTHORIZE] -> [EXECUTE] -> [RECORD] -> [VERIFY]
+-------------------------------------------------------------+
                              |
                     Execution Adapters
                              |
                              v
+-------------------------------------------------------------+
|                   Infrastructure Backends                   |
|       (HPE Morpheus, Kubernetes, Private Clouds, Tools)     |
+-------------------------------------------------------------+
```

---

## 2. Mapping MCP Tools to OASA Golden Path

| MCP Tool | OASA Golden Path Verb | Access Scope | Operational Behavior |
| :--- | :--- | :--- | :--- |
| `oasa.get_status` | Status / Health | Read-only | Returns gateway status, governance mode, and engine state |
| `oasa.discover` | **DISCOVER** | Read-only | Enumerates authorized target URIs and capabilities for the principal |
| `oasa.evaluate_action` | **AUTHORIZE** | Read/Evaluate | Evaluates policy; issues single-use authorization token on `ALLOW` |
| `oasa.execute_action` | **EXECUTE** | Controlled Write | Atomically redeems token and dispatches to target execution adapter |
| `oasa.get_action` | **RECORD** | Read-only | Returns the signed cryptographic Action Envelope by `action_id` |
| `oasa.get_provenance` | **RECORD** | Read-only | Returns immutable execution provenance and audit metadata |
| `oasa.verify_evidence`| **VERIFY** | Stateless Verify | Validates Ed25519 signature & SHA-256 hashes independently |
| `oasa.request_human_approval` | **HUMAN OVERRIDE** | Approval Gate | Submits sensitive action for explicit human supervisor review |

---

## 3. Normative Security Invariants

### 3.1 Fail-Closed Authentication (`MCP-SEC-001`)
The MCP adapter MUST NOT execute or evaluate actions without a trusted principal resolved from the transport session or authentication context. Unauthenticated callers MUST be rejected with `PermissionError`.

### 3.2 Anti-Theater Enforcement (`MCP-SEC-002`)
When an action is evaluated as `DENY` (e.g. destructive commands or unauthorized targets), the MCP server and client MUST guarantee that zero calls reach the underlying provider. A verifiable denial record must be produced.

### 3.3 Atomic Token Redemption (`MCP-SEC-003`)
Tokens issued during `oasa.evaluate_action` are single-use. Replay attempts or parameter mutations MUST be rejected with `TOKEN_ALREADY_CONSUMED` or `TOKEN_PARAMETER_MISMATCH`.

### 3.4 Bidirectional Governance (`MCP-SEC-004`)
When SovereignStack consumes external MCP servers using `GovernedMCPClient`, all external tool calls MUST pass through `evaluate_action` prior to execution. Emergency kill-switch activation halts all external invocations immediately.

---

## 4. MCP Context Resources & Prompts

### Resources
- `sovereignstack://standards/oasa`: Canonical OASA specification text.
- `sovereignstack://policies/core`: Core production safety policies.
- `sovereignstack://actions/{action_id}`: JSON representation of the Action Envelope.

### Prompts
- `governed_deployment_review`: Structured prompt guiding models to perform discovery, policy check, and authorization prior to deployment.
- `security_audit_review`: Structured prompt guiding models to audit Ed25519 signatures, hash bindings, and provider linkage.
