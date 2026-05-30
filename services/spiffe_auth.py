from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os, logging

logger = logging.getLogger(__name__)

def spiffe_enabled() -> bool:
    return os.getenv("SPIFFE_ENABLED", "").lower() in ("1", "true", "yes")

async def require_spiffe_or_skip(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> dict | None:
    """Validate SPIFFE JWT SVID as Bearer token. Returns caller SPIFFE ID dict or None if SPIFFE disabled."""
    if not spiffe_enabled():
        return None

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing SPIFFE JWT SVID")

    token = credentials.credentials
    try:
        import jwt

        # In production, validate offline with SPIRE bundle; here we do basic decode
        # trusting that SPIRE-issued JWT SVIDs are signed by the SPIRE server key
        if os.getenv("SPIFFE_DEV_SKIP_VERIFICATION", "false").lower() != "true":
            raise HTTPException(status_code=500, detail="SPIFFE JWT signature verification is required in production. Set SPIFFE_DEV_SKIP_VERIFICATION=true for dev.")
        
        if os.getenv("OASA_ENFORCE_AUTH", "STRICT").upper() == "STRICT":
            raise HTTPException(status_code=500, detail="Cannot skip SPIFFE JWT signature verification when OASA_ENFORCE_AUTH=STRICT.")

        logger.warning("SECURITY WARNING: SPIFFE JWT signature verification is disabled. Do not use this in production without SPIRE bundle validation.")
        payload = jwt.decode(token, options={"verify_signature": False})
        spiffe_id = payload.get("sub", "")
        if not spiffe_id.startswith("spiffe://"):
            raise HTTPException(status_code=403, detail="Invalid SPIFFE ID in token")
        return {"spiffe_id": spiffe_id, "claims": payload}
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=403, detail=f"SPIFFE JWT validation failed: {e}")

def authorized_spiffe_ids(allowed: list[str] | None = None):
    """Factory for FastAPI dependency that restricts callers by SPIFFE ID prefix."""
    allowed = allowed or ["spiffe://sovereign.stack/"]

    async def _check(identity: dict | None = Depends(require_spiffe_or_skip)):
        if identity is None:
            # SPIFFE disabled — allow all
            return {"spiffe_id": "unknown", "claims": {}}
        sid = identity["spiffe_id"]
        if not any(sid.startswith(a) for a in allowed):
            raise HTTPException(
                status_code=403,
                detail=f"SPIFFE ID {sid} not authorized. Allowed prefixes: {allowed}",
            )
        return identity

    return _check
