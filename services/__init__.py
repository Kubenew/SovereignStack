# Services package for SovereignStack

"""SovereignStack microservices.

Each service is a standalone FastAPI application designed to run as an
independent container.  This package-level ``__init__`` re-exports the
public helpers that are shared across services (SPIFFE auth, merkle
auditing, event logging, etc.).
"""

__all__ = [
    # Auth / identity
    "spiffe_auth",
    # Federation sync primitives
    "event_log",
    "sync_engine",
    "crdt",
    # Audit infrastructure
    "merkle_audit",
]
