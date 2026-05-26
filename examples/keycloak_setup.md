# Keycloak SSO Integration Guide (OASA-Auth)

SovereignStack includes an **auto-imported Keycloak realm** via Docker Compose, so you can start with zero manual configuration.

---

## Quick Start (Automated)

The realm, clients, roles, and users are imported automatically from `config/keycloak/sovereign-realm.json` when you run:

```bash
docker compose up -d
```

Keycloak will be available at `http://localhost:8083`.

### Pre-Configured Test Users

| Username | Password | Roles |
|---|---|---|
| `sovereign-admin` | `admin123` | `inference:write`, `inference:read`, `audit:read` |
| `sovereign-analyst` | `analyst123` | `inference:read` |

### Get a Token

```bash
curl -X POST http://localhost:8083/realms/sovereign/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sovereign-gateway" \
  -d "username=sovereign-admin" \
  -d "password=admin123" \
  -d "grant_type=password"
```

### Use the Token with the Gateway

```bash
TOKEN="<access_token from above>"

curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role":"user","content":"Hello"}],
    "oasa_compliance_lock": true
  }'
```

### Token Claims Structure

The access token contains roles in the `realm_access.roles` field:

```json
{
  "sub": "...",
  "realm_access": {
    "roles": ["inference:write", "inference:read", "audit:read"]
  },
  "preferred_username": "sovereign-admin"
}
```

---

## Manual Configuration (Custom Realm)

If you need a custom realm configuration beyond the auto-imported defaults:

### 1. Create the Sovereign Realm

1. Open the Keycloak Admin Console at `http://localhost:8083`.
2. Log in with `admin` / `admin`.
3. In the top-left dropdown, click **Create Realm**.
4. Set the **Realm Name** to `sovereign`.
5. Click **Create**.

### 2. Create the Gateway Client

1. Go to **Clients** → **Create client**.
2. Configure:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `sovereign-gateway`
   - **Name**: `OASA API Gateway`
3. Enable **Standard flow** and **Service accounts roles**.
4. Set **Valid redirect URIs**: `http://localhost:8080/*`
5. Click **Save**.

### 3. Define Roles

Under the `sovereign-gateway` client → **Roles** tab, create:

| Role | Permission |
|---|---|
| `inference:write` | Run chat completions and query models |
| `inference:read` | Read-only model access |
| `audit:read` | Retrieve audit logs |

### 4. Map Roles to Token Claims

1. Go to **Client scopes** → `sovereign-gateway-dedicated` → **Mappers**.
2. Click **Configure new mapper** → **User Client Role**.
3. Set **Token Claim Name** to `roles`.
4. Enable for ID token, access token, and userinfo.
5. Click **Save**.

### 5. Update Sovereign Config

```yaml
services:
  gateway:
    identity:
      enabled: true
      provider: "keycloak"
      issuer_url: "http://keycloak:8083/realms/sovereign"
      client_id: "sovereign-gateway"
```

---

## RBAC Enforcement

The gateway enforces these role checks:

| Required Role | Endpoint | Effect if Missing |
|---|---|---|
| `inference:write` | `POST /v1/chat/completions` | 403 Forbidden |
| `audit:read` | `GET /audit/log` (future) | 403 Forbidden |

---

## Troubleshooting

**Invalid token errors:**
```bash
# Verify the token is valid
curl -s http://localhost:8083/realms/sovereign/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Realm not found:**
```bash
# Check Keycloak logs
docker compose logs keycloak
```
