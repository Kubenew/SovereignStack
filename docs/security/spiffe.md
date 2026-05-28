# SPIFFE / SPIRE Workload Identity Integration

SovereignStack uses **SPIFFE** (Secure Production Identity Framework for Everyone) via **SPIRE** to provide cryptographically verifiable workload identities to every service in the mesh.

---

## Why SPIFFE?

| Problem | SPIFFE Solution |
|---|---|
| Services need to authenticate each other | X.509 SVIDs with mTLS |
| Audit logs need workload attribution | Each audit event includes the SPIFFE ID |
| Policy enforcement needs caller identity | JWT SVIDs carry workload identity |
| No shared secrets across services | SPIRE issues short-lived SVIDs automatically |
| Node identity vs workload identity | Separate tiers: node (RFC 0003) + workload (SPIFFE) |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        SOVEREIGN MESH                               │
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  SPIRE       │    │  SPIRE       │    │              │         │
│  │  Server      │◄──►│  Agent       │    │  Gateway     │         │
│  │  (CA + Reg)  │    │  (Attestor)  │◄───│  Service     │         │
│  │  :8084       │    │  UDS         │    │  :8080       │         │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘         │
│         │                   │                                       │
│         │         ┌─────────▼─────────┐                             │
│         │         │  Workload API     │   /var/run/spire/agent.sock│
│         │         │  (gRPC over UDS)  │                             │
│         │         └───────────────────┘                             │
│         │                                                           │
│         └───────────────────────────────────────────────────────────┘
│                      Registration entries map                      │
│                      unix:uid → spiffe://sovereign.stack/service/*  │
└───────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role |
|---|---|
| **SPIRE Server** | Certificate Authority, registration store, SVID issuer |
| **SPIRE Agent** | Node attestation, workload API endpoint, SVID caching |
| **Workload API** | gRPC socket at `/var/run/spire/agent.sock` |
| **spiffe Python package** | Client library for the Workload API |

---

## Workload Identity Mapping

Services are identified by their Unix UID:

| Service | UID | SPIFFE ID |
|---|---|---|
| Gateway | 1001 | `spiffe://sovereign.stack/service/gateway` |
| Memory | 1002 | `spiffe://sovereign.stack/service/memory` |
| Ingest | 1003 | `spiffe://sovereign.stack/service/ingest` |

Registration entries are created via `scripts/register-spire-entries.sh`.

---

## Integration Points

### 1. Audit Attribution

Every audit event now includes the SPIFFE ID of the calling service:

```json
{
  "event_id": "evt-9102",
  "type": "inference.completion",
  "spiffe_id": "spiffe://sovereign.stack/service/gateway",
  "action": "..."
}
```

### 2. Inter-service Authentication

Services authenticate each other using **SPIFFE JWT SVIDs** carried as Bearer tokens in HTTP headers.

**Caller side** — the gateway fetches a JWT SVID and includes it in requests to memory and ingest:

```python
from services.spiffe_helper import spiffe_ctx

headers = spiffe_ctx.get_auth_header("memory")
# Use headers in requests to the memory service
# Headers: {"Authorization": "Bearer <JWT_SVID>"}
```

**Callee side** — memory and ingest services validate incoming JWT SVIDs via a FastAPI dependency:

```python
from services.spiffe_auth import authorized_spiffe_ids

# Only allow callers with specific SPIFFE ID prefixes
_memory_auth = authorized_spiffe_ids(
    allowed=[
        "spiffe://sovereign.stack/service/gateway",
        "spiffe://sovereign.stack/service/ingest",
    ]
)

@app.post("/embed")
def embed(req: EmbedRequest, identity: dict = Depends(_memory_auth)):
    ...
```

**Authorized caller matrix:**

| Service | Allowed Caller SPIFFE IDs |
|---|---|
| memory | `service/gateway`, `service/ingest`, `service/admin` |
| ingest | `service/gateway`, `service/admin` |

When `SPIFFE_ENABLED=false` (default), all inter-service calls proceed without authentication. When enabled, requests without a valid JWT SVID receive a `401` (missing token) or `403` (invalid/unauthorized SPIFFE ID) response.

The auth module is defined in [`services/spiffe_auth.py`](/services/spiffe_auth.py) and provides:

- `require_spiffe_or_skip()` — FastAPI dependency that validates JWT SVIDs when SPIFFE is enabled, skips when disabled
- `authorized_spiffe_ids(allowed)` — Factory for dependency that additionally checks the SPIFFE ID prefix

### 3. Health & Identity Endpoint

Each service exposes a `/spiffe` endpoint:

```bash
curl http://localhost:8080/spiffe
{
  "spiffe_status": "available",
  "workload_identity": "spiffe://sovereign.stack/service/gateway",
  "trust_domain": "sovereign.stack"
}
```

---

## Configuration

### Service Environment

```yaml
SPIFFE_ENABLED: "true"
SPIRE_SOCKET_PATH: "/var/run/spire/agent.sock"
SPIFFE_TRUST_DOMAIN: "sovereign.stack"
```

### SPIRE Server

See [`config/spire/server.conf`](/config/spire/server.conf) — trust domain `sovereign.stack`, CA key `ec-p384`, SQLite registration store.

### SPIRE Agent

See [`config/spire/agent.conf`](/config/spire/agent.conf) — join token attestation, Unix workload attestation by UID.

---

## Deployment

SPIRE is deployed as part of the Docker Compose stack:

```bash
# Generate a join token
docker compose exec spire-server ./bin/spire-server token generate -spiffeID spiffe://sovereign.stack/spire/agent/join_token

# Set the token in .env
SPIRE_JOIN_TOKEN=<token>

# Register workload entries
./scripts/register-spire-entries.sh

# Verify registration
docker compose exec spire-server ./bin/spire-server entry list

# Check gateway's SPIFFE identity
curl http://localhost:8080/spiffe
```

---

## Security Considerations

| Concern | Control |
|---|---|
| Socket snooping | UDS permissions `0600`, owned by `root:spire` |
| Token theft | Short TTL (1h), automatic rotation |
| UID spoofing | Requires root to spoof UID in container |
| Server compromise | SPIRE CA key encrypted at rest |
| Agent compromise | SVIDs scoped to registered workloads only |

---

## See Also

- [RFC 0003: Node Identity](/rfcs/0003-node-identity.md)
- [SPIFFE Standard](https://spiffe.io)
- [SPIRE Documentation](https://spiffe.io/docs/latest/spire-about/)
- [Services: spiffe_helper.py](/services/spiffe_helper.py)
