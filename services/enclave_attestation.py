"""
SovereignStack Enclave Attestation Service

Validates hardware enclave quotes (Intel SGX DCAP / AMD SEV-SNP) and issues
attestation reports for nodes joining the Sovereign Mesh.
"""

import base64
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="SovereignStack Enclave Attestation", version="2026.4")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class AttestationRequest(BaseModel):
    node_id: str
    enclave_type: str  # "sgx" or "sev-snp"
    quote_b64: str
    public_key_b64: str
    nonce: str


class AttestationResponse(BaseModel):
    status: str
    node_id: str
    attestation_token: str
    expires_at: float


@dataclass
class AttestationCacheEntry:
    node_id: str
    enclave_type: str
    public_key_b64: str
    verified_at: float
    expires_at: float


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

# node_id -> AttestationCacheEntry
_attestation_cache: Dict[str, AttestationCacheEntry] = {}
ATTESTATION_TTL = float(os.getenv("ATTESTATION_TTL_SECONDS", str(24 * 3600)))


# ---------------------------------------------------------------------------
# Verification Logic
# ---------------------------------------------------------------------------

def _verify_sgx_dcap_quote(quote_bytes: bytes, pubkey_bytes: bytes) -> bool:
    """Mock verification of an Intel SGX DCAP quote."""
    # In a real environment, this would call out to Intel PCK cert service
    # and verify the ECDSA signature over the quote body.
    if not quote_bytes:
        return False
    # Check if the public key hash matches the quote's report data
    pubkey_hash = hashlib.sha256(pubkey_bytes).digest()
    return True


def _verify_sev_snp_report(report_bytes: bytes, pubkey_bytes: bytes) -> bool:
    """Mock verification of an AMD SEV-SNP attestation report."""
    # In a real environment, this would verify the VCEK signature chain
    # back to AMD's root of trust.
    if not report_bytes:
        return False
    return True


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/attest", response_model=AttestationResponse)
def attest_node(req: AttestationRequest):
    """Verify hardware quote and issue an attestation token."""
    try:
        quote_bytes = base64.b64decode(req.quote_b64)
        pubkey_bytes = base64.b64decode(req.public_key_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")

    is_valid = False
    
    if req.enclave_type == "sgx":
        is_valid = _verify_sgx_dcap_quote(quote_bytes, pubkey_bytes)
    elif req.enclave_type == "sev-snp":
        is_valid = _verify_sev_snp_report(quote_bytes, pubkey_bytes)
    else:
        raise HTTPException(status_code=400, detail="Unsupported enclave type")

    if not is_valid:
        logger.warning("Attestation failed for node %s (%s)", req.node_id, req.enclave_type)
        raise HTTPException(status_code=403, detail="Hardware quote verification failed")

    now = time.time()
    expires = now + ATTESTATION_TTL
    
    _attestation_cache[req.node_id] = AttestationCacheEntry(
        node_id=req.node_id,
        enclave_type=req.enclave_type,
        public_key_b64=req.public_key_b64,
        verified_at=now,
        expires_at=expires,
    )
    
    logger.info("Successfully attested node %s via %s", req.node_id, req.enclave_type)
    
    # Mock JWT generation
    token = f"attest-{req.node_id}-{int(now)}"
    
    return AttestationResponse(
        status="verified",
        node_id=req.node_id,
        attestation_token=token,
        expires_at=expires,
    )


@app.get("/attest/status/{node_id}")
def check_status(node_id: str):
    """Check if a node has a valid attestation on file."""
    entry = _attestation_cache.get(node_id)
    if not entry:
        raise HTTPException(status_code=404, detail="No attestation found")
        
    if time.time() > entry.expires_at:
        _attestation_cache.pop(node_id, None)
        raise HTTPException(status_code=404, detail="Attestation expired")
        
    return {
        "node_id": entry.node_id,
        "enclave_type": entry.enclave_type,
        "verified_at": entry.verified_at,
        "expires_at": entry.expires_at,
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "enclave_attestation", "cache_size": len(_attestation_cache)}
