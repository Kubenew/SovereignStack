#!/usr/bin/env python3
"""Generate a proof-of-concept ZK alignment proof."""

import hashlib
import json
import os

def hash_values_document(doc: bytes) -> str:
    return hashlib.sha256(doc).hexdigest()

def generate_proof(values_doc: bytes, decision: bytes) -> dict:
    values_hash = hash_values_document(values_doc)
    decision_digest = hashlib.sha256(decision).hexdigest()

    # Proof-of-concept: the proof blob is a simple Merkle-like commitment.
    # In production this would be a real ZK-SNARK.
    combined = values_doc + decision + b"alignment-proof-domain-v1"
    proof_blob = hashlib.sha256(combined).hexdigest()

    return {
        "values_hash": values_hash,
        "decision_digest": decision_digest,
        "proof_blob": proof_blob,
        "public_inputs": [],
        "version": "0.1.0-poc",
    }

def verify_proof(proof: dict, values_doc: bytes, decision: bytes) -> bool:
    expected_values_hash = hash_values_document(values_doc)
    if proof["values_hash"] != expected_values_hash:
        return False
    expected_decision_digest = hashlib.sha256(decision).hexdigest()
    if proof["decision_digest"] != expected_decision_digest:
        return False
    # Recompute proof blob
    combined = values_doc + decision + b"alignment-proof-domain-v1"
    expected_blob = hashlib.sha256(combined).hexdigest()
    return proof["proof_blob"] == expected_blob


def main():
    values_doc = b"ethical-guidelines-v1-do-not-harm"
    decision = b"approve-loan-application-42"

    proof = generate_proof(values_doc, decision)
    print("Generated alignment proof:")
    print(json.dumps(proof, indent=2))

    assert verify_proof(proof, values_doc, decision), "Verification failed"
    print("\n[PASS] Proof verified successfully.")

    # Demonstrate tamper detection
    tampered_decision = b"approve-loan-application-43"
    assert not verify_proof(proof, values_doc, tampered_decision), "Tamper check failed"
    print("[PASS] Tampered decision correctly rejected.")


if __name__ == "__main__":
    main()
