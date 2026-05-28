# Enterprise Platform

SovereignStack Enterprise Platform provides support contract management, SLA tracking, managed updates, deployment auditing, and licensing for regulated deployments.

---

## Support Contracts

Contracts define the commercial relationship between the node operator and SovereignStack. Each contract specifies tier, SLA response time, licensed features, and node count.

| Tier | SLA | Features |
|---|---|---|
| **Community** | Best-effort | Basic support, community forum |
| **Standard** | 8-hour response | Email support, audit logs, 8h SLA |
| **Enterprise** | 4-hour response | Phone support, managed updates, deployment audits, SSO |
| **Enterprise Plus** | 1-hour response | Dedicated engineer, custom integration, on-prem deployment |

### API

```bash
# View active contract
curl http://localhost:8085/enterprise/contract

# Create/activate a contract
curl -X POST http://localhost:8085/enterprise/contract \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Acme Corp", "tier": "enterprise", "max_nodes": 5}'

# Get SLA metrics
curl http://localhost:8085/enterprise/sla

# Get license info
curl http://localhost:8085/enterprise/license
```

---

## Support Tickets

Create and manage support tickets linked to your active contract.

```bash
# Create a support ticket
curl -X POST http://localhost:8085/enterprise/ticket \
  -H "Content-Type: application/json" \
  -d '{"subject": "GPU failure", "description": "Node 3 GPU not responding", "severity": "high"}'

# List all tickets
curl http://localhost:8085/enterprise/tickets

# Get ticket details
curl http://localhost:8085/enterprise/tickets/{id}

# Resolve a ticket
curl -X POST http://localhost:8085/enterprise/tickets/{id}/resolve
```

Tickets automatically receive an SLA deadline based on the active contract's `sla_response_hours`. If not resolved by the deadline, it's marked as an SLA breach.

---

## Managed Updates

Check for and apply platform updates.

```bash
# Check for available updates
curl http://localhost:8085/enterprise/updates/check

# Apply an update (requires confirmation)
curl -X POST http://localhost:8085/enterprise/updates/apply \
  -H "Content-Type: application/json" \
  -d '{"update_id": "v2026.4", "confirm": true}'
```

---

## Deployment Audit

Run a comprehensive deployment audit to verify enterprise readiness.

```bash
# Run all checks and print results
python tools/audit_deployment.py validate

# Generate audit report JSON
python tools/audit_deployment.py report --output data/deployment-audit.json
```

### Checks performed

| Check | Description |
|---|---|
| Python version | Runtime version |
| Docker | Docker availability |
| Environment config | `.env` or `.env.example` present |
| Data directories | `data/`, `data/ingest/`, `data/memory/` exist |
| Audit log | `audit.log` exists and has entries |
| Merkle tree | `merkle_tree.json` integrity |
| Network isolation | Isolated bridge network configured |
| Helm chart | Helm CLI available |
| Compliance report | L2 conformance report exists |

---

## Data Persistence

All enterprise data is stored in `{DATA_DIR}/`:

| File | Purpose |
|---|---|
| `contracts.json` | Active support contracts |
| `support_tickets.json` | Support ticket history |
| `update_history.json` | Managed update audit trail |
| `deployment-audit.json` | Generated deployment audit reports |

---

## Compliance Mapping

| Requirement | How Enterprise Platform Fulfills It |
|---|---|
| **GDPR Art. 32** | Deployment audit verifies security controls |
| **HIPAA 164.312(b)** | Audit log + Merkle tree checked in every audit |
| **SOC 2 CC6** | Contracts + licensing enforce access boundaries |
| **OASA L3** | Enterprise tier required for L3 certification |

---

## See Also

- [Services: enterprise_service.py](/services/enterprise_service.py)
- [Tool: audit_deployment.py](/tools/audit_deployment.py)
- [Deployment Guide](/docs/deployment/)
- [Compliance Framework](/docs/compliance/index.md)
- [Security Overview](/docs/security/index.md)
