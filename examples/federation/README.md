# Multi-Node Federation Example

This example demonstrates a 3-node SovereignStack federation spanning EU, US, and Asia jurisdictions with a CRDT-based sync relay and Merkle audit aggregation.

## Topology

```
EU-Frankfurt (L3 Strict) ──┐
                            ├── Federation Relay ── Audit Aggregator
US-Silicon (L2 Secure)  ───┤
                            │
Asia-Tokyo (L1 Ready)   ───┘
```

## Quick Start

```bash
# Launch all nodes
docker compose -f examples/federation/docker-compose.federation.yml up -d

# Check health of each node
curl http://localhost:8081/health  # EU
curl http://localhost:8082/health  # US
curl http://localhost:8083/health  # Asia

# Route a session across the mesh
curl -X POST http://localhost:8081/route \
  -H "Content-Type: application/json" \
  -d '{"session": "session://demo", "capability": "capability://math-reasoning"}'

# Check federation sync status
curl http://localhost:9090/status

# View aggregated audit log
curl http://localhost:9091/audit
```

## Jurisdiction Rules

| Node | Jurisdiction | Trust Level | Data Residency |
|------|-------------|-------------|----------------|
| EU-Frankfurt | eu-de | L3 Strict | GDPR — no export |
| US-Silicon | us-ca | L2 Secure | CCPA — controlled |
| Asia-Tokyo | jp | L1 Ready | Local processing |

## Teardown

```bash
docker compose -f examples/federation/docker-compose.federation.yml down -v
```
