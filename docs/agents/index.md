# Agent Orchestration Layer

The Agent Orchestration Layer manages the lifecycle, scheduling, memory attachment, and secure execution of sovereign AI agents — providing a "Kubernetes for agents" abstraction over the runtime.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      AGENT ORCHESTRATION LAYER                        │
│                                                                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                 │
│  │  Scheduler   │   │  Registry   │   │  Supervisor  │                 │
│  │  (placement) │   │  (catalog)  │   │  (lifecycle) │                 │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                 │
│         │                 │                  │                         │
│  ┌──────▼─────────────────▼──────────────────▼──────┐                 │
│  │                 Agent Executor                      │               │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │               │
│  │  │  Agent A  │  │  Agent B  │  │  Agent C  │       │               │
│  │  │  (sandbox)│  │  (sandbox)│  │  (sandbox)│       │               │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘         │               │
│  └───────┼──────────────┼──────────────┼──────────────┘               │
│          │              │              │                               │
│  ┌───────▼──────────────▼──────────────▼──────────────┐               │
│  │              Sovereign Runtime                       │             │
│  │  (Memory, Inference, Policy, Audit)                  │             │
│  └──────────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Responsibility |
|---|---|
| **Registry** | Agent catalog, versioning, metadata store |
| **Scheduler** | Placement decisions, resource allocation, scaling |
| **Supervisor** | Lifecycle management, health monitoring, restart policy |
| **Executor** | Sandboxed runtime for agent processes |
| **Memory Attacher** | Attaches vector memory / KV cache contexts |

---

## Agent Lifecycle

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ SUBMIT  │───►│ PENDING  │───►│ RUNNING  │───►│ PAUSED   │───►│ COMPLETE │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │              │                              │
                     │              │                              │
                     ▼              ▼                              ▼
               ┌──────────┐   ┌──────────┐                  ┌──────────┐
               │ REJECTED │   │ FAILED   │                  │ ARCHIVED │
               └──────────┘   └──────────┘                  └──────────┘
```

| State | Meaning |
|---|---|
| **SUBMIT** | Agent manifest received, validation pending |
| **PENDING** | Queued for scheduling |
| **RUNNING** | Active in sandboxed executor |
| **PAUSED** | Suspended (resource preemption or user request) |
| **COMPLETE** | Finished successfully |
| **FAILED** | Terminated with error |
| **REJECTED** | Failed validation or policy check |
| **ARCHIVED** | Result stored, agent metadata retained |

---

## Agent Manifest

Agents are defined via an OASA-compliant manifest:

```yaml
apiVersion: sovereign.ai/v1
kind: Agent
metadata:
  name: document-analyzer
  version: 1.2.0
spec:
  model: "sovereign-llama3"
  memory:
    attach:
      - vector-store: "corpus-v1"
        access: "read-only"
      - kv-cache: "session-cache"
        access: "read-write"
  tools:
    - type: "function"
      name: "search_documents"
      schema:
        parameters:
          query: string
  policy:
    runtime: "gvisor"
    allow_network: false
    allow_filesystem: false
    max_memory_mb: 2048
    max_duration_seconds: 300
  schedule:
    replicas: 1
    restart: "on-failure"
    resources:
      cpu: "2"
      memory: "2Gi"
      vram_gb: 4
```

---

## Scheduling

The scheduler places agents onto available compute nodes based on:

| Criteria | Weight |
|---|---|
| Model affinity (model already loaded) | High |
| VRAM availability | High |
| Data locality (memory co-location) | Medium |
| Policy isolation requirements | Medium |
| Load balancing | Low |

### Scheduling Policy

```yaml
scheduling:
  strategy: "binpack"            # binpack | spread | random
  preemption: true               # Allow preemption of lower-priority agents
  priority_classes:
    critical: 1000
    production: 500
    batch: 100
    background: 10
```

---

## Memory Attachment

Agents can attach to three memory tiers:

| Tier | Backend | Persistence | Attachment Mode |
|---|---|---|---|
| **Vector Store** | `memory_service` | Disk (AES-256-GCM) | read-only / read-write |
| **KV Cache** | `memory_service` | Volatile | read-write |
| **Event Log** | Append-only log | Disk (immutable) | append-only |

Memory is attached before the agent starts and detached on completion.

---

## Secure Execution

Every agent runs in an isolated sandbox:

| Control | Implementation |
|---|---|
| **Runtime isolation** | gVisor (or Firecracker for L3 cert) |
| **Network policy** | egress blocked by default, opt-in per agent |
| **Filesystem** | Ephemeral tmpfs, no host mount |
| **Memory isolation** | Process-level cgroups + memory limits |
| **Audit** | All tool calls logged to event log |
| **Timeout** | Enforced via `max_duration_seconds` |

---

## Agent-to-Agent Communication

Agents communicate via a **message bus** with verified identity:

```json
{
  "from": "agent:document-analyzer@node-eu-fr1",
  "to": "agent:summary-writer@node-eu-fr1",
  "type": "request",
  "payload": {"task": "summarize", "doc_id": "doc-456"},
  "signature": "MEUCIQD..."
}
```

Messages are:
- Authenticated via agent identity (SPIFFE-compatible)
- Encrypted in transit (mTLS)
- Audited to the event log
- Rate-limited per agent

---

## Observability

| Metric | Source |
|---|---|
| Agent count (running/pending/failed) | Supervisor |
| Scheduling latency | Scheduler |
| Memory attach/detach duration | Memory Attacher |
| Tool call count & latency | Executor |
| Sandbox CPU/memory usage | cgroups exporter |

All metrics exported via OpenTelemetry to the configured collector.

---

## "Kubernetes for Agents" Vision

The Agent Orchestration Layer mirrors Kubernetes concepts:

| Kubernetes | Sovereign Agents |
|---|---|
| Pod | Agent instance |
| Deployment | Agent manifest with replicas |
| Service | Agent message bus endpoint |
| Namespace | Agent isolation domain |
| RBAC | Agent identity + policy |
| Horizontal Pod Autoscaler | Agent scheduler (model-aware) |
| ConfigMap / Secret | Attached memory (vector store) |

This enables familiar operational patterns: declarative manifests, desired-state reconciliation, health-based restart, and resource-aware scheduling — applied to AI agent workloads instead of containers.

---

## See Also

- [Agent Spec](/specs/) (planned)
- [Runtime Architecture](/docs/runtime/index.md)
- [Memory Architecture](/docs/memory/index.md)
- [Security Threat Model](/docs/security/threat-model.md)
