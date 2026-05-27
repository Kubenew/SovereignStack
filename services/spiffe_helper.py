import os, logging

logger = logging.getLogger(__name__)

SPIRE_SOCKET_PATH = os.getenv("SPIRE_SOCKET_PATH", "/var/run/spire/agent.sock")
SPIFFE_TRUST_DOMAIN = os.getenv("SPIFFE_TRUST_DOMAIN", "sovereign.stack")
SPIFFE_ENABLED = os.getenv("SPIFFE_ENABLED", "false").lower() == "true"

class SpiffeContext:
    def __init__(self):
        self.client = None
        self._ready = False

    def init(self):
        if not SPIFFE_ENABLED:
            logger.info("SPIFFE disabled via SPIFFE_ENABLED env — using OIDC-only auth")
            return
        try:
            from spiffe.workloadapi.workload_api_client import WorkloadApiClient
            self.client = WorkloadApiClient(socket_path=SPIRE_SOCKET_PATH)
            svid = self.client.fetch_x509_svid()
            self.spiffe_id = str(svid.spiffe_id)
            self._ready = True
            logger.info("SPIFFE initialized — workload identity: %s", self.spiffe_id)
        except Exception as e:
            self.client = None
            self._ready = False
            logger.warning("SPIFFE unavailable (SPIRE Agent not running?): %s — falling back to OIDC-only", e)

    @property
    def ready(self):
        return self._ready

    @property
    def identity(self):
        if self._ready and self.client:
            try:
                svid = self.client.fetch_x509_svid()
                return str(svid.spiffe_id)
            except Exception:
                return None
        return None

    def fetch_jwt_svid(self, audience: str) -> str | None:
        if not self._ready or not self.client:
            return None
        try:
            svid = self.client.fetch_jwt_svid(audience)
            return svid.token
        except Exception as e:
            logger.warning("Failed to fetch JWT SVID for audience=%s: %s", audience, e)
            return None

    def get_auth_header(self, audience: str) -> dict[str, str] | None:
        token = self.fetch_jwt_svid(audience)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None

    def close(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass

spiffe_ctx = SpiffeContext()
