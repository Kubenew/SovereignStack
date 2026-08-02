"""Gateway configuration via environment variables.

All config is read from the environment at startup.
No .env files, no YAML — just environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass(frozen=True)
class GatewayConfig:
    """Configuration for the OASA Gateway.

    All values are read from environment variables with ``OASA_`` prefix.
    """

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8080

    # --- Upstream LLM ---
    upstream_base_url: str = "https://api.openai.com"
    upstream_api_key: str = ""  # If set, gateway injects this key; else passthrough

    # --- Audit ---
    data_dir: Path = field(default_factory=lambda: Path("./oasa-data"))
    keypair_path: Path = field(default_factory=lambda: Path("./oasa-data/gateway-key.json"))

    # --- Behavior ---
    log_request_bodies: bool = True  # If False, only hashes are stored
    log_response_bodies: bool = True
    max_body_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    @classmethod
    def from_env(cls) -> GatewayConfig:
        """Load configuration from environment variables.

        Each field maps to ``OASA_<FIELD_NAME_UPPERCASE>``, e.g.:
        - ``OASA_HOST`` → host
        - ``OASA_PORT`` → port
        - ``OASA_UPSTREAM_BASE_URL`` → upstream_base_url
        """
        return cls(
            host=os.environ.get("OASA_HOST", "0.0.0.0"),
            port=int(os.environ.get("OASA_PORT", "8080")),
            upstream_base_url=os.environ.get(
                "OASA_UPSTREAM_BASE_URL", "https://api.openai.com"
            ),
            upstream_api_key=os.environ.get("OASA_UPSTREAM_API_KEY", ""),
            data_dir=Path(os.environ.get("OASA_DATA_DIR", "./oasa-data")),
            keypair_path=Path(
                os.environ.get("OASA_KEYPAIR_PATH", "./oasa-data/gateway-key.json")
            ),
            log_request_bodies=os.environ.get(
                "OASA_LOG_REQUEST_BODIES", "true"
            ).lower() == "true",
            log_response_bodies=os.environ.get(
                "OASA_LOG_RESPONSE_BODIES", "true"
            ).lower() == "true",
            max_body_size_bytes=int(
                os.environ.get("OASA_MAX_BODY_SIZE_BYTES", str(10 * 1024 * 1024))
            ),
        )

    def ensure_data_dir(self) -> None:
        """Create the data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
