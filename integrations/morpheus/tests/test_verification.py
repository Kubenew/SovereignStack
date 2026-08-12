import pytest
import os
import tempfile
import json
from tools.verify_evidence import verify_evidence

def test_evidence_tampering():
    """
    Test 5: Evidence tampering
    Modify an event in the valid chain and expect ChainVerifier to fail.
    """
    # Create a temporary tampered evidence file
    valid_evidence = {
        "platform": "hpe-morpheus-vm-essentials",
        "profile": "morpheus-vm-essentials-9.0",
        "workload": "vm://morpheus/12345",
        "operation": "provision",
        "authorization": "allowed",
        "provenance": {
            "chain_valid": True,
            "entries": 7
        },
        "evidence": {
            "integrity": "valid",
            "signature": "invalid",  # Tampered signature!
            "policy": "compliant"
        },
        "conformance": {
            "core-0.1": "PASS",
            "morpheus-0.1": "PASS"
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as f:
        json.dump(valid_evidence, f)
        temp_path = f.name

    try:
        # Verify should fail
        result = verify_evidence(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)

def test_morpheus_api_mismatch():
    """
    Test 6: Morpheus/API mismatch
    SovereignStack authorized VM X, but Morpheus reports VM Y.
    """
    # This logic would be implemented in a verifier cross-checking the provenance
    # against the authorization record. Here we mock the result state.
    mismatched_evidence = {
        "platform": "hpe-morpheus-vm-essentials",
        "profile": "morpheus-vm-essentials-9.0",
        "workload": "vm://morpheus/Y",  # Mismatch! Authorized X, executed Y.
        "operation": "provision",
        "authorization": "allowed",
        "provenance": {
            "chain_valid": True,
            "entries": 7
        },
        "evidence": {
            "integrity": "invalid", # Marked invalid due to mismatch
            "signature": "valid",
            "policy": "compliant"
        },
        "conformance": {
            "core-0.1": "PASS",
            "morpheus-0.1": "FAIL"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as f:
        json.dump(mismatched_evidence, f)
        temp_path = f.name

    try:
        result = verify_evidence(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)
