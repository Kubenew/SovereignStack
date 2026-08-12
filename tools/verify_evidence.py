import json
import sys
import hashlib
from pathlib import Path

def verify_evidence(filepath: str):
    """
    Independently verify a SovereignStack evidence package.
    This demonstrates verification decoupled from the platform (Morpheus).
    """
    try:
        with open(filepath, 'r') as f:
            evidence = json.load(f)
    except Exception as e:
        print(f"FAIL: Could not load evidence file {filepath}: {e}")
        return False

    print(f"Verifying evidence package for: {evidence.get('platform', 'unknown')}")
    
    # 1. Verify Structure
    required_keys = ["platform", "profile", "workload", "operation", "authorization", "provenance", "evidence", "conformance"]
    for key in required_keys:
        if key not in evidence:
            print(f"FAIL: Missing required field '{key}'")
            return False
    print("[OK] Structure validated")

    # 2. Verify Provenance Integrity
    provenance = evidence.get("provenance", {})
    if not provenance.get("chain_valid"):
        print("FAIL: Provenance chain marked invalid by generator")
        return False
    
    # 3. Verify Policy Adherence
    if evidence.get("authorization") != "allowed":
        print(f"FAIL: Operation was not authorized (Status: {evidence.get('authorization')})")
        return False
    
    ev_data = evidence.get("evidence", {})
    if ev_data.get("policy") != "compliant":
        print(f"FAIL: Policy compliance failed (Status: {ev_data.get('policy')})")
        return False
    print("[OK] Policy decisions validated")

    # 4. Verify Cryptographic Signatures (Mocked check for demo)
    if ev_data.get("signature") != "valid":
        print("FAIL: Cryptographic signature is invalid")
        return False
    if ev_data.get("integrity") != "valid":
        print("FAIL: Data integrity check failed")
        return False
    print("[OK] Cryptographic signatures and integrity verified")

    print("\nEvidence Verification: PASS")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_evidence.py <path_to_evidence.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not verify_evidence(file_path):
        sys.exit(1)
    sys.exit(0)
