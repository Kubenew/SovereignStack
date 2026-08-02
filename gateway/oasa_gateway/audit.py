"""Core audit logic: hash, sign, and append events to the Merkle log.

This is the heart of the OASA Gateway. It takes raw request/response data,
creates a structured AuditEvent, signs it with the gateway's Ed25519 key,
and appends the signed envelope to the Merkle log.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ss_core.types import ContentHash, Timestamp
from ss_crypto.envelope import SignedEnvelope
from ss_crypto.hashing import hash_content_hex
from ss_crypto.keys import KeyPair
from ss_cas.merkle import MerkleLog
from ss_cas.sqlite import SqliteCAS

from oasa_gateway.config import GatewayConfig
from oasa_gateway.models import AuditEvent, AuditStats

logger = logging.getLogger("oasa.audit")


class AuditEngine:
    """The audit engine: signs events and appends them to the Merkle log.

    Manages the gateway's keypair, the CAS, and the Merkle log.
    Thread-safe for reads; writes are serialized by SQLite.
    """

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        config.ensure_data_dir()

        # Initialize or load the gateway signing key
        self.keypair = self._init_keypair(config.keypair_path)

        # CAS for storing signed envelopes
        cas_path = config.data_dir / "cas.db"
        self.cas = SqliteCAS(cas_path)

        # Merkle log for the append-only audit trail
        merkle_path = config.data_dir / "merkle.db"
        self.merkle = MerkleLog(merkle_path)

        logger.info(
            "Audit engine initialized: pubkey=%s, data_dir=%s",
            self.keypair.public_key.fingerprint,
            config.data_dir,
        )

    @staticmethod
    def _init_keypair(keypair_path: Path) -> KeyPair:
        """Load or generate the gateway's Ed25519 signing key."""
        if keypair_path.exists():
            kp = KeyPair.load(keypair_path)
            logger.info("Loaded existing keypair: %s", kp.public_key.fingerprint)
            return kp

        # Generate a new keypair
        kp = KeyPair.generate()
        keypair_path.parent.mkdir(parents=True, exist_ok=True)
        kp.save(keypair_path)
        logger.info("Generated new keypair: %s", kp.public_key.fingerprint)
        return kp

    def record_event(
        self,
        request_body: bytes,
        response_body: bytes,
        request_method: str = "POST",
        request_path: str = "/v1/chat/completions",
        response_status: int = 200,
        model: str = "unknown",
        caller_identity: str = "anonymous",
        upstream_latency_ms: int = 0,
    ) -> tuple[AuditEvent, SignedEnvelope]:
        """Record an AI API call in the audit log.

        1. Creates an AuditEvent with hashes of the request/response.
        2. Serializes the event to JSON.
        3. Signs it with the gateway's Ed25519 key.
        4. Appends the signed envelope to the Merkle log.
        5. Stores the signed envelope in the CAS.

        Args:
            request_body: Raw request bytes.
            response_body: Raw response bytes.
            request_method: HTTP method.
            request_path: Request URL path.
            response_status: HTTP response status code.
            model: LLM model name.
            caller_identity: API key fingerprint or user ID.
            upstream_latency_ms: Upstream response time.

        Returns:
            Tuple of (AuditEvent, SignedEnvelope).
        """
        now = datetime.now(timezone.utc).isoformat()

        # Build the event
        event = AuditEvent(
            timestamp=now,
            request_hash=hash_content_hex(request_body),
            request_body=request_body.decode("utf-8", errors="replace")
            if self.config.log_request_bodies
            else "",
            request_method=request_method,
            request_path=request_path,
            response_hash=hash_content_hex(response_body),
            response_body=response_body.decode("utf-8", errors="replace")
            if self.config.log_response_bodies
            else "",
            response_status=response_status,
            model=model,
            caller_identity=caller_identity,
            upstream_latency_ms=upstream_latency_ms,
        )

        # Serialize, sign, and append to the Merkle log
        event_json = event.model_dump_json().encode("utf-8")
        envelope = SignedEnvelope.create(event_json, self.keypair)

        # Append the envelope's JSON to the Merkle log
        envelope_bytes = envelope.to_json().encode("utf-8")
        leaf_hash, index = self.merkle.append(envelope_bytes)
        root = self.merkle.root()

        # Update the event with Merkle position
        event.merkle_index = index
        event.merkle_root = str(root)

        # Store the envelope in CAS
        self.cas.put(envelope_bytes)

        logger.info(
            "Recorded event %s at index %d (root=%s)",
            event.event_id,
            index,
            root.hex[:16],
        )

        return event, envelope

    def get_stats(self) -> AuditStats:
        """Get summary statistics for the audit log."""
        size = self.merkle.size
        root = self.merkle.root()

        # Get time range
        oldest = None
        newest = None
        if size > 0:
            first = self.merkle.get_leaf(0)
            if first:
                try:
                    env_data = json.loads(first[1])
                    payload = json.loads(
                        __import__("base64").b64decode(env_data["payload"])
                    )
                    oldest = payload.get("timestamp")
                except (json.JSONDecodeError, KeyError):
                    pass

            last = self.merkle.get_leaf(size - 1)
            if last:
                try:
                    env_data = json.loads(last[1])
                    payload = json.loads(
                        __import__("base64").b64decode(env_data["payload"])
                    )
                    newest = payload.get("timestamp")
                except (json.JSONDecodeError, KeyError):
                    pass

        return AuditStats(
            total_events=size,
            merkle_root=str(root),
            oldest_event=oldest,
            newest_event=newest,
            data_dir=str(self.config.data_dir),
        )

    def close(self) -> None:
        """Close database connections."""
        self.cas.close()
        self.merkle.close()
