"""Pydantic models for audit events.

An AuditEvent is the structured record of a single AI API call,
including the full request/response, timing, and Merkle tree position.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from ss_core.types import AuditEventId


class AuditEvent(BaseModel):
    """A single AI API call audit record.

    This is serialized to JSON, signed, and appended to the Merkle log.
    """

    model_config = {"arbitrary_types_allowed": True}

    event_id: str = Field(
        default_factory=lambda: str(AuditEventId.generate()),
        description="UUID v7 identifier for this event",
    )
    timestamp: str = Field(
        description="ISO 8601 UTC timestamp of the event",
    )

    # Request
    request_hash: str = Field(description="SHA-256 hash of the request body")
    request_body: str = Field(default="", description="Full request body (or empty if redacted)")
    request_method: str = Field(default="POST", description="HTTP method")
    request_path: str = Field(default="/v1/chat/completions", description="Request path")

    # Response
    response_hash: str = Field(description="SHA-256 hash of the response body")
    response_body: str = Field(default="", description="Full response body (or empty if redacted)")
    response_status: int = Field(default=200, description="HTTP status code")

    # Metadata
    model: str = Field(default="unknown", description="LLM model name (e.g. gpt-4o)")
    caller_identity: str = Field(
        default="anonymous",
        description="API key fingerprint or user ID of the caller",
    )
    upstream_latency_ms: int = Field(
        default=0, description="Upstream LLM response time in milliseconds"
    )

    # Merkle tree position (set after appending to the log)
    merkle_index: int = Field(default=-1, description="Leaf index in the Merkle log")
    merkle_root: str = Field(default="", description="Merkle root hash after append")


class AuditStats(BaseModel):
    """Summary statistics for the audit log."""

    total_events: int
    merkle_root: str
    oldest_event: str | None = None
    newest_event: str | None = None
    data_dir: str = ""
