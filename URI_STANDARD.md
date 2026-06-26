# SovereignStack URI Standard

**Version:** 1.0
**Status:** Draft

## URI Schemes

```
agent://<uuid-or-did>
org://<org-name>                   # Organization
session://<session-id>
memory://<memory-id>
knowledge://<knowledge-id>
reason://<reason-trace-id>
artifact://<artifact-id>
contract://<task-id>                # Agent contract
event://<event-id>                  # Event record
workflow://<workflow-id>
capability://<capability-id>
policy://<policy-id>
node://<node-id>
robot://<device-id>                 # Physical device (RFC-0011)
leaf://<fabric>/<leaf-id>          # Fabric leaf switch (RFC-0030)
spine://<fabric>/<spine-id>        # Fabric spine switch (RFC-0030)
rail://<fabric>/<rail-id>          # Fabric rail (RFC-0030)
fabric://<fabric-name>             # Named AI fabric (RFC-0030)
topology://<cluster-name>          # Named topology graph (RFC-0030)
link://<fabric>/<link-id>          # Named fabric link (RFC-0032)
tel://<fabric>/<event-id>          # Telemetry event (RFC-0033)
kv://<fabric>/<node-id>/<session>/<head>  # KV cache object (RFC-0034)
gateway://<location>               # Federation gateway (RFC-0035)
mem://<fabric>/<node>/<tier>       # Memory pool (RFC-0036)
profile://<profile-name>           # Cluster profile (RFC-0037)
model://<registry>/<name>          # AI model identifier (RFC-0040)
dataset://<registry>/<name>        # Dataset identifier (RFC-0040)
training://<cluster>/<run-id>      # Training run (RFC-0040)
evaluation://<cluster>/<eval-id>   # Model evaluation (RFC-0040)
audit-pkg://<node>/<date>          # Audit evidence package
continuity://<cluster>/<service>   # AI continuity manifest (RFC-0052)
recovery://<cluster>/<incident>    # Recovery procedure record (RFC-0050)
failover://<cluster>/<date>/<evt>  # Failover event log (RFC-0051)
playbook://<cluster>/<name>        # Recovery playbook (RFC-0050)
```

## Resolution Rules

1. Local resolution preferred (Offline First)
2. Federation resolution only if explicitly allowed
3. All URIs are **case-sensitive**
4. DID (Decentralized Identifier) support planned

## Examples

- `agent://a1b2c3d4-e5f6-...`
- `org://acme`
- `contract://task-88`
- `event://evt-99`
- `robot://drone-12`
- `knowledge://sha256:abc123...`
- `capability://delegated:read:memory://xyz`
- `leaf://zcube-a/leaf03`
- `spine://fabric-a/spine01`
- `rail://zcube-a/rail7`
- `fabric://zcube-a`
- `topology://cluster-prod`
- `tel://zcube-a/evt-001`
- `kv://zcube-a/gpu-003/session-abc/head-0`
- `gateway://eu-frankfurt`
- `mem://zcube-a/gpu-003/hbm`
- `profile://zcube-standard-v1`
- `model://huggingface/Qwen/Qwen2.5-72B`
- `dataset://huggingface/c4`
- `training://zcube-a/run-0042`
- `evaluation://zcube-a/eval-007`
- `audit-pkg://node-001/2026-06-03`
- `continuity://zcube-a/legal-agent`
- `recovery://zcube-a/incident-42`
- `failover://zcube-a/2026-06-03/evt-001`
- `playbook://zcube-a/gpu-failure`

This standard enforces **Principle 4 — Address Everything**.
