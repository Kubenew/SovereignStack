"""Tests for GraphQL API layer."""
import os
os.environ["SPIFFE_ENABLED"] = "false"
os.environ["OASA_ALLOW_MOCK_TOKENS"] = "true"
os.environ["OASA_ENFORCE_AUTH"] = "DEVELOPMENT"
os.environ["OASA_ENFORCE_POLICY"] = "DEVELOPMENT"
os.environ["COMPUTE_URL"] = "http://mock-compute"
os.environ["INFERENCE_BACKEND"] = "legacy"

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from services.gateway_service import app

client = TestClient(app)


class TestGraphQLQuery:
    def test_health_query(self):
        resp = client.post("/graphql", json={"query": "{ health { status service spiffeEnabled } }"})
        assert resp.status_code == 200
        data = resp.json()["data"]["health"]
        assert data["status"] == "ok"
        assert data["service"] == "gateway"
        assert data["spiffeEnabled"] is False

    def test_spiffe_identity_query(self):
        resp = client.post("/graphql", json={"query": "{ spiffeIdentity { spiffeStatus workloadIdentity trustDomain } }"})
        assert resp.status_code == 200
        data = resp.json()["data"]["spiffeIdentity"]
        assert data["spiffeStatus"] == "unavailable"
        assert data["workloadIdentity"] is None

    def test_oidc_config_query(self):
        resp = client.post("/graphql", json={"query": "{ oidcConfig { issuer } }"})
        assert resp.status_code == 200
        data = resp.json()["data"]["oidcConfig"]
        assert data["issuer"] is not None

    def test_schema_introspection(self):
        resp = client.post("/graphql", json={"query": "{ __schema { queryType { name } mutationType { name } } }"})
        assert resp.status_code == 200
        schema = resp.json()["data"]["__schema"]
        assert schema["queryType"]["name"] == "Query"
        assert schema["mutationType"]["name"] == "Mutation"


class TestGraphQLMutation:
    @patch("services.graphql_schema.requests.post")
    def test_chat_completion_mutation(self, mock_post):
        mock_compute = MagicMock()
        mock_compute.status_code = 200
        mock_compute.json.return_value = {"response": "This is a local response"}
        mock_post.return_value = mock_compute

        resp = client.post("/graphql", json={
            "query": """
                mutation Chat($input: ChatCompletionInput!) {
                    chatCompletion(input: $input) {
                        success
                        payload {
                            id
                            model
                            choices { index message { role content } }
                        }
                        error
                    }
                }
            """,
            "variables": {
                "input": {
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "oasaComplianceLock": True,
                    "useRag": False,
                }
            },
        })
        assert resp.status_code == 200
        result = resp.json()["data"]["chatCompletion"]
        assert result["success"] is True
        assert result["payload"]["model"] == "Qwen/Qwen2.5-7B-Instruct"
        assert len(result["payload"]["choices"]) == 1
        assert result["payload"]["choices"][0]["message"]["role"] == "assistant"
        assert "This is a local response" in result["payload"]["choices"][0]["message"]["content"]

    def test_chat_completion_missing_lock(self):
        """GraphQL mutation should fail without compliance lock."""
        resp = client.post("/graphql", json={
            "query": """
                mutation Chat($input: ChatCompletionInput!) {
                    chatCompletion(input: $input) { success error }
                }
            """,
            "variables": {
                "input": {
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "oasaComplianceLock": False,
                }
            },
        })
        assert resp.status_code == 200
        result = resp.json()["data"]["chatCompletion"]
        assert result["success"] is False
        assert "compliance lock" in result["error"].lower()

    @patch("services.graphql_schema.requests.post")
    @patch.dict(os.environ, {"OASA_ENFORCE_POLICY": "STRICT"})
    def test_chat_completion_policy_violation(self, mock_post):
        """GraphQL should block prompts with PII."""
        mock_compute = MagicMock()
        mock_compute.status_code = 200
        mock_compute.json.return_value = {"response": "response"}
        mock_post.return_value = mock_compute

        resp = client.post("/graphql", json={
            "query": """
                mutation Chat($input: ChatCompletionInput!) {
                    chatCompletion(input: $input) { success error }
                }
            """,
            "variables": {
                "input": {
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": "My SSN is 123-45-6789"}],
                    "oasaComplianceLock": True,
                }
            },
        })
        assert resp.status_code == 200
        result = resp.json()["data"]["chatCompletion"]
        assert result["success"] is False
        assert "SSN" in result["error"]

    def test_graphql_health_rest_parity(self):
        """GraphQL health should match REST health endpoint."""
        rest = client.get("/health").json()
        gql = client.post("/graphql", json={"query": "{ health { status service spiffeEnabled } }"}).json()["data"]["health"]
        assert rest["status"] == gql["status"]
        assert rest["service"] == gql["service"]
        assert rest["spiffe_enabled"] == gql["spiffeEnabled"]
