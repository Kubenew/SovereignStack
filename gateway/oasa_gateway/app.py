"""FastAPI application factory for the OASA Gateway.

Creates the app, wires up the proxy routes, audit engine, and health endpoints.
"""

from __future__ import annotations

import hashlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response

from oasa_gateway.audit import AuditEngine
from oasa_gateway.config import GatewayConfig
from oasa_gateway.export import EvidenceExporter
from oasa_gateway.health import router as health_router
from oasa_gateway.proxy import LLMProxy

logger = logging.getLogger("oasa")


def create_app(config: GatewayConfig | None = None) -> FastAPI:
    """Create and configure the OASA Gateway FastAPI application.

    Args:
        config: Gateway configuration. If None, reads from environment.

    Returns:
        A fully configured FastAPI application.
    """
    if config is None:
        config = GatewayConfig.from_env()

    # These are initialized in the lifespan
    state: dict = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Initialize resources on startup, clean up on shutdown."""
        logger.info("Starting OASA Gateway on %s:%d", config.host, config.port)

        state["audit"] = AuditEngine(config)
        state["proxy"] = LLMProxy(config)
        state["exporter"] = EvidenceExporter(
            merkle=state["audit"].merkle,
            keypair=state["audit"].keypair,
        )

        yield

        # Shutdown
        logger.info("Shutting down OASA Gateway")
        await state["proxy"].close()
        state["audit"].close()

    app = FastAPI(
        title="OASA Gateway",
        description=(
            "Open AI Security API Gateway — immutable audit logging for AI API calls. "
            "Part of the SovereignStack project."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # --- Health endpoints ---
    app.include_router(health_router)

    # --- Audit stats ---
    @app.get("/audit/stats", summary="Audit log statistics", tags=["audit"])
    async def audit_stats() -> dict:
        """Return summary statistics about the audit log."""
        engine: AuditEngine = state["audit"]
        stats = engine.get_stats()
        return stats.model_dump()

    # --- Export endpoint ---
    @app.get("/audit/export", summary="Export evidence package", tags=["audit"])
    async def export_evidence(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Response:
        """Export an evidence package as a downloadable zip file.

        Query params:
            start_date: ISO date (e.g. 2026-07-31)
            end_date: ISO date (e.g. 2026-07-31)
        """
        exporter: EvidenceExporter = state["exporter"]
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            date_suffix = start_date or "all"
            output_path = Path(tmp) / f"oasa-evidence-{date_suffix}.zip"
            exporter.export(output_path, start_date, end_date)
            zip_bytes = output_path.read_bytes()

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=oasa-evidence-{date_suffix}.zip"
            },
        )

    # --- Merkle proof endpoint ---
    @app.get(
        "/audit/proof/{index}",
        summary="Get Merkle inclusion proof",
        tags=["audit"],
    )
    async def merkle_proof(index: int) -> dict:
        """Generate a Merkle inclusion proof for the event at the given index."""
        engine: AuditEngine = state["audit"]
        proof = engine.merkle.prove(index)
        return proof.to_dict()

    # --- Proxy catch-all for LLM API calls ---
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        summary="Proxy to upstream LLM",
        tags=["proxy"],
    )
    async def proxy_handler(request: Request, path: str) -> Response:
        """Transparent proxy: forwards to upstream, audits the round-trip."""
        proxy: LLMProxy = state["proxy"]
        engine: AuditEngine = state["audit"]

        # Proxy the request
        (
            request_body,
            response_body,
            status_code,
            model_name,
            latency_ms,
        ) = await proxy.proxy_request(request, f"/{path}")

        # Extract caller identity from auth header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            caller_id = f"key:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        else:
            caller_id = "anonymous"

        # Record in the audit log
        event, envelope = engine.record_event(
            request_body=request_body,
            response_body=response_body,
            request_method=request.method,
            request_path=f"/{path}",
            response_status=status_code,
            model=model_name,
            caller_identity=caller_id,
            upstream_latency_ms=latency_ms,
        )

        # Return the upstream response with OASA audit headers
        return proxy.build_response(
            response_body=response_body,
            status_code=status_code,
            event_id=event.event_id,
            content_hash=event.response_hash,
        )

    return app


# Default app instance for uvicorn
app = create_app()
