"""Health and readiness endpoints for the OASA Gateway."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, str]:
    """Basic liveness probe. Returns 200 if the process is running."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness check")
async def ready() -> dict[str, str]:
    """Readiness probe. Returns 200 when the gateway is ready to accept traffic.

    In future, this could check database connectivity and upstream availability.
    """
    return {"status": "ready"}
