#!/usr/bin/env python3
"""
OASA Certification Issuer

Issues a cryptographically signed oasa-certification.schema.json attestation
based on a passing compliance report.

Usage:
  python tools/issue_certification.py --report report.json --level L2 \\
      --subject-name "My Node" --subject-type node --output attestation.json
"""

import argparse
import base64
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path


def load_private_key(key_path: str):
    """Attempt to load an Ed25519 private key, or fallback to HMAC secret."""
    if key_path and os.path.exists(key_path):
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            with open(key_path, "rb") as f:
                return load_pem_private_key(f.read(), password=None)
        except Exception as exc:
            print(f"Warning: Failed to load private key from {key_path}: {exc}", file=sys.stderr)
    return None


def sign_payload(payload_bytes: bytes, private_key, hmac_secret: str) -> dict:
    """Sign payload with Ed25519 or HMAC-SHA256 fallback."""
    if private_key:
        try:
            from cryptography.hazmat.primitives import serialization
            sig = private_key.sign(payload_bytes)
            cert_chain = [
                base64.b64encode(
                    private_key.public_key().public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                ).decode("utf-8")
            ]
            return {
                "algorithm": "Ed25519",
                "digest": base64.b64encode(sig).decode("utf-8"),
                "certificate_chain": cert_chain
            }
        except Exception as exc:
            print(f"Warning: Ed25519 signing failed: {exc}, falling back to HMAC", file=sys.stderr)

    # HMAC fallback
    import hmac
    secret = hmac_secret.encode('utf-8')
    sig = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
    return {
        "algorithm": "HMAC-SHA256",
        "digest": base64.b64encode(sig).decode("utf-8"),
        "certificate_chain": ["hmac-fallback-key-id"]
    }


def main():
    parser = argparse.ArgumentParser(description="Issue OASA Certification")
    parser.add_argument("--report", required=True, type=Path, help="Path to compliance report JSON")
    parser.add_argument("--level", required=True, choices=["L1", "L2", "L3"], help="Certification level to issue")
    parser.add_argument("--subject-name", required=True, help="Name of the certified subject")
    parser.add_argument("--subject-version", default="1.0.0", help="Version of the certified subject")
    parser.add_argument("--subject-type", required=True, choices=["inference-engine", "gateway", "memory-store", "ingestion-pipeline", "platform", "node", "hardware-appliance", "runtime", "federation"], help="Type of implementation")
    parser.add_argument("--output", type=Path, default=Path("certification-attestation.json"), help="Output path")
    parser.add_argument("--key", help="Path to issuer PEM private key")
    parser.add_argument("--hmac-secret", default="sovereign-dev-secret", help="Fallback HMAC secret for testing")
    args = parser.parse_args()

    if not args.report.exists():
        print(f"Error: Report file {args.report} does not exist.")
        return 1

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error: Failed to parse report JSON: {exc}")
        return 1

    # Verify pass rate
    summary = report.get("summary", {})
    failed = summary.get("failed", 1)
    if failed > 0:
        print(f"Error: Cannot issue certification for a report with {failed} failing tests.")
        return 1

    # Add registry_url if available
    registry_url = os.getenv("CERTIFICATION_REGISTRY_URL", "")
    if registry_url:
        attestation["certification"]["registry_entry"] = f"{registry_url}/certification/registry"

    if report.get("level") != args.level:
        print(f"Warning: Report level ({report.get('level')}) does not match requested level ({args.level}).")

    now = datetime.datetime.now(datetime.timezone.utc)
    expires = now + datetime.timedelta(days=365)

    attestation = {
        "oasa_version": report.get("oasa_version", "2026.1"),
        "certification": {
            "level": args.level,
            "status": "active",
            "issued": now.isoformat(),
            "expires": expires.isoformat(),
            "badge_url": f"https://raw.githubusercontent.com/Kubenew/SovereignStack/main/badges/oasa-{args.level.lower()}.svg"
        },
        "subject": {
            "name": args.subject_name,
            "version": args.subject_version,
            "type": args.subject_type
        },
        "tests": {
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "suite_version": report.get("report_version", "1.0"),
            "details": report.get("results", [])
        }
    }

    # Generate canonical JSON string for signing
    canonical_payload = json.dumps(attestation, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    private_key = load_private_key(args.key)
    sig_block = sign_payload(canonical_payload, private_key, args.hmac_secret)
    
    attestation["signature"] = sig_block

    args.output.write_text(json.dumps(attestation, indent=2), encoding="utf-8")
    print(f"Successfully issued OASA {args.level} certification to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
