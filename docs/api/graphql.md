# GraphQL API

SovereignStack exposes a GraphQL API alongside the REST API, available at `/graphql` on the gateway service. This provides an alternative interface for queries and mutations with native schema introspection.

---

## Endpoint

```
POST /graphql
```

The gateway supports both REST (`/v1/chat/completions`) and GraphQL (`/graphql`) on the same server, using the same authentication, rate limiting, audit logging, and business logic.

---

## Schema

### Queries

#### `health`

Returns the gateway health status.

```graphql
query {
  health {
    status
    service
    spiffeEnabled
  }
}
```

Response:
```json
{
  "data": {
    "health": {
      "status": "ok",
      "service": "gateway",
      "spiffeEnabled": false
    }
  }
}
```

#### `spiffeIdentity`

Returns the SPIFFE workload identity.

```graphql
query {
  spiffeIdentity {
    spiffeStatus
    workloadIdentity
    trustDomain
  }
}
```

#### `oidcConfig`

Returns the OIDC issuer configuration.

```graphql
query {
  oidcConfig {
    issuer
  }
}
```

### Mutations

#### `chatCompletion`

Processes an inference request, same logic as `POST /v1/chat/completions` REST endpoint.

```graphql
mutation Chat($input: ChatCompletionInput!) {
  chatCompletion(input: $input) {
    success
    payload {
      id
      model
      choices {
        index
        message {
          role
          content
        }
      }
    }
    error
  }
}
```

Variables:
```json
{
  "input": {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "oasaComplianceLock": true,
    "useRag": true,
    "temperature": 0.2,
    "maxTokens": 1024
  }
}
```

Response:
```json
{
  "data": {
    "chatCompletion": {
      "success": true,
      "payload": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "choices": [
          {
            "index": 0,
            "message": {
              "role": "assistant",
              "content": "Hello! How can I help you today?"
            }
          }
        ]
      },
      "error": null
    }
  }
}
```

#### Error Handling

On failure, the mutation returns `success: false` with an `error` message:

```json
{
  "data": {
    "chatCompletion": {
      "success": false,
      "payload": null,
      "error": "Unauthorized. A valid Keycloak/OIDC Bearer token is required."
    }
  }
}
```

Error scenarios covered: auth failure, RBAC denial, policy violation, compliance lock missing, rate limiting, compute backend failure.

---

## Authentication

Authentication uses the same OIDC JWT validation as the REST API. Pass the Bearer token in the `Authorization` header:

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Authorization: Bearer <oidc-token>" \
  -H "Content-Type: application/json" \
  -d '{ "query": "{ health { status } }" }'
```

---

## Schema Introspection

The GraphQL endpoint supports full schema introspection for tooling compatibility:

```graphql
query {
  __schema {
    queryType { name }
    mutationType { name }
    types { name kind }
  }
}
```

---

## Python Client Example

```python
import requests

url = "http://localhost:8080/graphql"
token = "<your-oidc-token>"

query = """
mutation Chat($input: ChatCompletionInput!) {
  chatCompletion(input: $input) {
    success
    payload { id model choices { message { content } } }
    error
  }
}
"""

variables = {
    "input": {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": "What is data sovereignty?"}],
        "oasaComplianceLock": True,
    }
}

resp = requests.post(url, json={"query": query, "variables": variables},
                     headers={"Authorization": f"Bearer {token}"})
print(resp.json()["data"]["chatCompletion"])
```

---

## See Also

- [REST API](/docs/architecture/index.md)
- [Gateway Service](/services/gateway_service.py)
- [GraphQL Schema](/services/graphql_schema.py)
