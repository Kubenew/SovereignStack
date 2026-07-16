# SovereignStack URI Standard

**Version:** 2.0
**Status:** Draft
**Related:** [SIRA](SIRA.md) · [Object Model](OBJECT_MODEL.md)

## URI Schemes

### Cognitive Objects

```
mind://<mind-id>                        # Root persistent cognitive state
reason://<reason-trace-id>              # Verifiable reasoning graph node
goal://<goal-id>                        # Active objective
belief://<belief-id>                    # Held proposition
knowledge://<knowledge-id>              # Long-term versioned facts
```

### Operational Objects

```
agent://<uuid-or-did>                   # Autonomous reasoning entity
session://<session-id>                  # Bounded cognitive process
workflow://<workflow-id>                # Executable process
artifact://<artifact-id>               # Produced artifact
contract://<task-id>                    # Agent contract
event://<event-id>                     # Event record
checkpoint://<checkpoint-id>           # Execution state snapshot
```

### Governance Objects

```
policy://<policy-id>                   # Governance rules
capability://<capability-id>           # Permission token
evidence://<evidence-id>               # Verifiable audit evidence
```

### Federation Objects

```
org://<org-name>                       # Organization
node://<node-id>                       # Physical or virtual host
fabric://<fabric-name>                 # Named AI fabric (RFC-0030)
topology://<cluster-name>              # Named topology graph (RFC-0030)
gateway://<location>                   # Federation gateway (RFC-0035)
routing://<route-id>                   # Cognitive routing entry
```

### Infrastructure Objects

```
memory://<memory-id>                   # Memory object
robot://<device-id>                    # Physical device (RFC-0011)
leaf://<fabric>/<leaf-id>              # Fabric leaf switch (RFC-0030)
spine://<fabric>/<spine-id>            # Fabric spine switch (RFC-0030)
rail://<fabric>/<rail-id>              # Fabric rail (RFC-0030)
link://<fabric>/<link-id>              # Named fabric link (RFC-0032)
tel://<fabric>/<event-id>              # Telemetry event (RFC-0033)
kv://<fabric>/<node-id>/<session>/<head>   # KV cache object (RFC-0034)
mem://<fabric>/<node>/<tier>           # Memory pool (RFC-0036)
profile://<profile-name>               # Cluster profile (RFC-0037)
model://<registry>/<name>              # AI model identifier (RFC-0040)
dataset://<registry>/<name>            # Dataset identifier (RFC-0040)
training://<cluster>/<run-id>          # Training run (RFC-0040)
evaluation://<cluster>/<eval-id>       # Model evaluation (RFC-0040)
```

### Recovery & Continuity Objects

```
audit-pkg://<node>/<date>              # Audit evidence package
continuity://<cluster>/<service>       # AI continuity manifest (RFC-0052)
recovery://<cluster>/<incident>        # Recovery procedure record (RFC-0050)
failover://<cluster>/<date>/<evt>      # Failover event log (RFC-0051)
playbook://<cluster>/<name>            # Recovery playbook (RFC-0050)
```

### Cognitive Economics Objects

```
compute://<allocation-id>              # GPU/CPU allocation
bandwidth://<allocation-id>            # Network capacity
storage://<allocation-id>              # Persistent storage
energy://<allocation-id>               # Power consumption budget
```

## Resolution Rules

1. Local resolution preferred (Offline First)
2. Federation resolution only if explicitly allowed
3. All URIs are **case-sensitive**
4. DID (Decentralized Identifier) support planned
5. Content-addressed URIs (e.g., `mind://sha256:abc...`) enable portable, verifiable references

## Examples

### Cognitive
- `mind://enterprise`
- `mind://sha256:7a92ff01...`
- `reason://sha256:abc123`
- `goal://quarterly-revenue-target`
- `belief://market-growth-positive`
- `knowledge://sha256:abc123...`

### Operational
- `agent://a1b2c3d4-e5f6-...`
- `agent://reasoning/math`  (semantic anycast)
- `session://finance`
- `contract://task-88`
- `event://evt-99`
- `checkpoint://session-abc/step-42`

### Governance
- `policy://gdpr-eu`
- `capability://delegated:read:memory://xyz`
- `evidence://audit-report-2026-q2`

### Federation
- `org://acme`
- `node://homelab-1`
- `fabric://zcube-a`
- `topology://cluster-prod`
- `gateway://eu-frankfurt`
- `routing://mesh/verifier-model`

### Infrastructure
- `robot://drone-12`
- `leaf://zcube-a/leaf03`
- `spine://fabric-a/spine01`
- `rail://zcube-a/rail7`
- `link://zcube-a/link-leaf01-spine01`
- `tel://zcube-a/evt-001`
- `kv://zcube-a/gpu-003/session-abc/head-0`
- `mem://zcube-a/gpu-003/hbm`
- `profile://zcube-standard-v1`
- `model://huggingface/Qwen/Qwen2.5-72B`
- `dataset://huggingface/c4`
- `training://zcube-a/run-0042`
- `evaluation://zcube-a/eval-007`

### Recovery
- `audit-pkg://node-001/2026-06-03`
- `continuity://zcube-a/legal-agent`
- `recovery://zcube-a/incident-42`
- `failover://zcube-a/2026-06-03/evt-001`
- `playbook://zcube-a/gpu-failure`

### Economics
- `compute://zcube-a/alloc-001`
- `bandwidth://zcube-a/stream-042`
- `storage://zcube-a/pool-7`
- `energy://zcube-a/budget-q3`

This standard enforces **Principle 4 — Address Everything**.
