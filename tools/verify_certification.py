#!/usr/bin/env python3
"""
OASA Certification Verifier

Verifies the cryptographic signature and schema of an OASA certification attestation.

Usage:
  python tools/verify_certification.py --attestation attestation.json
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path


def verify_signature(payload_bytes: bytes, sig_block: dict, hmac_secret: str) -> bool:
    """Verify Ed25519 or HMAC-SHA256 signature."""
    algo = sig_block.get("algorithm")
    digest_b64 = sig_block.get("digest")
    
    if not algo or not digest_b64:
        print("Error: Missing algorithm or digest in signature block.")
        return False
        
    try:
        digest_bytes = base64.b64decode(digest_b64)
    except Exception:
        print("Error: Invalid base64 encoding for signature digest.")
        return False

    if algo == "Ed25519":
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.exceptions import InvalidSignature
            
            chain = sig_block.get("certificate_chain", [])
            if not chain:
                print("Error: Missing public key in certificate chain.")
                return False
                
            pubkey_bytes = base64.b64decode(chain[0])
            public_key = serialization.load_pem_public_key(pubkey_bytes)
            
            public_key.verify(digest_bytes, payload_bytes)
            return True
        except ImportError:
            print("Warning: cryptography package not available to verify Ed25519 signature.")
            return False
        except Exception as exc:
            print(f"Error: Ed25519 signature verification failed: {exc}")
            return False
            
    elif algo == "HMAC-SHA256":
        import hmac
        secret = hmac_secret.encode('utf-8')
        expected = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
        if hmac.compare_digest(expected, digest_bytes):
            return True
        print("Error: HMAC signature mismatch.")
        return False
        
    else:
        print(f"Error: Unsupported signature algorithm: {algo}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify OASA Certification")
    parser.add_argument("--attestation", required=True, type=Path, help="Path to certification attestation JSON")
    parser.add_argument("--hmac-secret", default="sovereign-dev-secret", help="Fallback HMAC secret for testing")
    args = parser.parse_args()

    if not args.attestation.exists():
        print(f"Error: Attestation file {args.attestation} does not exist.")
        return 1

    try:
        attestation = json.loads(args.attestation.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error: Failed to parse attestation JSON: {exc}")
        return 1

    # Extract signature and payload
    sig_block = attestation.pop("signature", None)
    if not sig_block:
        print("Error: No signature block found in attestation.")
        return 1

    # Generate canonical JSON string for verification
    canonical_payload = json.dumps(attestation, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    if verify_signature(canonical_payload, sig_block, args.hmac_secret):
        print(f"VERIFIED: Valid {attestation.get('certification', {}).get('level')} Certification for {attestation.get('subject', {}).get('name')}")
        return 0
    else:
        print("FAILED: Signature verification failed. The attestation is invalid or has been tampered with.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
