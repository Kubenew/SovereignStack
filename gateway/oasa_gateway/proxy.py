"""Transparent reverse proxy for upstream LLM APIs.

Routes requests to OpenAI, Anthropic, or any compatible API.
Captures full request/response bodies for audit logging.
Supports SSE (Server-Sent Events) streaming passthrough.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import AsyncGenerator

import httpx
from fastapi import Request, Response
from fastapi.responses import StreamingResponse

from oasa_gateway.config import GatewayConfig

logger = logging.getLogger("oasa.proxy")


class LLMProxy:
    """Transparent reverse proxy for LLM API calls.

    Forwards requests to the configured upstream, captures bodies,
    and returns responses to the caller.
    """

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.upstream_base_url,
            timeout=httpx.Timeout(120.0, connect=10.0),
            follow_redirects=True,
        )

    async def proxy_request(
        self, request: Request, path: str
    ) -> tuple[bytes, bytes, int, str, int]:
        """Proxy a request to the upstream LLM and capture the full round-trip.

        Args:
            request: The incoming FastAPI request.
            path: The target path on the upstream (e.g. /v1/chat/completions).

        Returns:
            Tuple of:
                - request_body: Raw request bytes
                - response_body: Full response bytes (accumulated for SSE)
                - status_code: HTTP status code from upstream
                - model_name: LLM model name extracted from the request
                - latency_ms: Upstream response time in milliseconds
        """
        # Read the full request body
        request_body = await request.body()

        # Build upstream headers — passthrough caller's auth or inject gateway's
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        if self.config.upstream_api_key:
            headers["authorization"] = f"Bearer {self.config.upstream_api_key}"

        # Extract model name from request body
        model_name = "unknown"
        try:
            import json
            body_json = json.loads(request_body)
            model_name = body_json.get("model", "unknown")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        # Forward to upstream
        start = time.monotonic()
        try:
            upstream_response = await self._client.request(
                method=request.method,
                url=path,
                content=request_body,
                headers=headers,
            )
        except httpx.HTTPError as e:
            logger.error("Upstream request failed: %s", e)
            raise

        latency_ms = int((time.monotonic() - start) * 1000)

        response_body = upstream_response.content
        status_code = upstream_response.status_code

        logger.info(
            "Proxied %s %s → %d (%dms, model=%s)",
            request.method,
            path,
            status_code,
            latency_ms,
            model_name,
        )

        return request_body, response_body, status_code, model_name, latency_ms

    def build_response(
        self,
        response_body: bytes,
        status_code: int,
        event_id: str,
        content_hash: str,
    ) -> Response:
        """Build a FastAPI Response with audit headers.

        Args:
            response_body: The upstream response body.
            status_code: The upstream status code.
            event_id: The OASA audit event ID.
            content_hash: SHA-256 hash of the response body.

        Returns:
            A FastAPI Response with added X-OASA-* headers.
        """
        return Response(
            content=response_body,
            status_code=status_code,
            media_type="application/json",
            headers={
                "X-OASA-Event-Id": event_id,
                "X-OASA-Content-Hash": content_hash,
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
