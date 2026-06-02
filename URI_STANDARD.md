# SovereignStack URI Standard

**Version:** 1.0
**Status:** Draft

## URI Schemes

```
agent://<uuid-or-did>
session://<session-id>
memory://<memory-id>
knowledge://<knowledge-id>
reason://<reason-trace-id>
artifact://<artifact-id>
workflow://<workflow-id>
capability://<capability-id>
policy://<policy-id>
node://<node-id>
leaf://<fabric>/<leaf-id>          # Fabric leaf switch (RFC-0030)
spine://<fabric>/<spine-id>        # Fabric spine switch (RFC-0030)
rail://<fabric>/<rail-id>          # Fabric rail (RFC-0030)
fabric://<fabric-name>             # Named AI fabric (RFC-0030)
topology://<cluster-name>          # Named topology graph (RFC-0030)
link://<fabric>/<link-id>          # Named fabric link (RFC-0032)
```

## Resolution Rules

1. Local resolution preferred (Offline First)
2. Federation resolution only if explicitly allowed
3. All URIs are **case-sensitive**
4. DID (Decentralized Identifier) support planned

## Examples

- `agent://a1b2c3d4-e5f6-...`
- `knowledge://sha256:abc123...`
- `capability://delegated:read:memory://xyz`
- `leaf://zcube-a/leaf03`
- `spine://fabric-a/spine01`
- `rail://zcube-a/rail7`
- `fabric://zcube-a`
- `topology://cluster-prod`

This standard enforces **Principle 4 — Address Everything**.
