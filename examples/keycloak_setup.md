# Keycloak SSO Integration Guide (OASA-Auth)

This guide walks through configuring **Keycloak** as the Identity Provider (IdP) for **SovereignStack**, enabling cryptographically validated OIDC authentication and Role-Based Access Control (RBAC).

---

## 1. Create the Sovereign Realm

1. Open the Keycloak Admin Console.
2. In the top-left dropdown menu, click **Create Realm**.
3. Set the **Realm Name** to `sovereign`.
4. Click **Create**.

---

## 2. Create the Gateway Client

1. In the left navigation bar, go to **Clients**.
2. Click **Create client**.
3. Configure the client parameters:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `sovereign-gateway`
   - **Name**: `OASA API Gateway`
4. Click **Next**.
5. Enable **Capability Config**:
   - **Client authentication**: `On` (Confidential Client)
   - **Authorization**: `Off`
   - **Authentication flow**: Check `Standard flow` and `Service accounts roles` (enabling client credentials authorization).
6. Click **Next**.
7. Configure **Login settings**:
   - **Root URL**: `http://localhost:8080` (or your Gateway host)
   - **Valid redirect URIs**: `http://localhost:8080/*`
   - **Web origins**: `*`
8. Click **Save**.

---

## 3. Define Roles & RBAC Scopes

SovereignStack maps permissions using roles inside the JWT claims payload.

1. Under the `sovereign-gateway` client dashboard, go to the **Roles** tab.
2. Click **Create role**.
3. Create the following three standard OASA roles:
   - `inference:write` — Permitted to run chat completions and query models.
   - `memory:write` — Permitted to insert documents into the vector store.
   - `compliance:read` — Permitted to retrieve audit logs.

---

## 4. Map Client Roles to Token Claims

To ensure the OASA Gateway can parse user permissions, map the roles into the Access Token claims payload.

1. Go to **Client scopes** in the left sidebar.
2. Click on the `sovereign-gateway-dedicated` scope (auto-created with the client).
3. Click the **Mappers** tab.
4. Click **Configure new mapper** and select **User Client Role**.
5. Configure the mapper parameters:
   - **Name**: `client roles`
   - **Client ID**: `sovereign-gateway`
   - **Token Claim Name**: `roles` (JSON Array format)
   - **Add to ID token**: `On`
   - **Add to access token**: `On`
   - **Add to userinfo**: `On`
6. Click **Save**.

---

## 5. Configure Gateway Environment

Once configured in Keycloak, retrieve the Client Secret and configure the Gateway environment variables or edit your `sovereign-stack.yaml` manifest:

```yaml
services:
  gateway:
    enabled: true
    listen: "0.0.0.0:8080"
    identity:
      enabled: true
      provider: "keycloak"
      issuer_url: "http://<keycloak-host>/auth/realms/sovereign"
      client_id: "sovereign-gateway"
```

Verify that authorization headers sent by clients look like:
```http
Authorization: Bearer <keycloak-generated-jwt>
```
