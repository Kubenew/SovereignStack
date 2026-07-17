use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// A zero-knowledge alignment proof.
///
/// Agents use this to prove they are acting in accordance with
/// organizational values without revealing sensitive internals.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZkAlignmentProof {
    /// SHA-256 commitment to the values document
    pub values_hash: [u8; 32],
    /// SHA-256 digest of the proposed action/decision
    pub decision_digest: [u8; 32],
    /// Opaque proof blob (placeholder for a real ZK-SNARK)
    pub proof_blob: Vec<u8>,
    /// Public inputs shared between prover and verifier
    pub public_inputs: Vec<u8>,
}

/// Verdict after verifying a ZK alignment proof.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AlignmentVerdict {
    Aligned,
    Misaligned(String),
    InvalidProof,
}

/// Verifier for ZK alignment proofs.
pub struct AlignmentVerifier {
    known_values_hashes: Vec<[u8; 32]>,
}

impl AlignmentVerifier {
    pub fn new(known_values: Vec<[u8; 32]>) -> Self {
        Self { known_values_hashes: known_values }
    }

    /// Verify an alignment proof.
    pub fn verify(&self, proof: &ZkAlignmentProof) -> AlignmentVerdict {
        if proof.proof_blob.is_empty() {
            return AlignmentVerdict::InvalidProof;
        }
        // Check that the values_hash is a recognized values document
        if !self.known_values_hashes.contains(&proof.values_hash) {
            return AlignmentVerdict::Misaligned("Unknown values document".into());
        }
        // Proof structural verification (placeholder for real ZK verification)
        if proof.proof_blob.len() < 16 {
            return AlignmentVerdict::InvalidProof;
        }
        AlignmentVerdict::Aligned
    }
}

/// Compute a SHA-256 commitment for a values document.
pub fn hash_values_document(doc: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(doc);
    let result = hasher.finalize();
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&result);
    arr
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_aligned() {
        let values = b"ethical-guidelines-v1";
        let vh = hash_values_document(values);
        let verifier = AlignmentVerifier::new(vec![vh]);

        let proof = ZkAlignmentProof {
            values_hash: vh,
            decision_digest: [1u8; 32],
            proof_blob: vec![0u8; 64],
            public_inputs: vec![],
        };
        assert_eq!(verifier.verify(&proof), AlignmentVerdict::Aligned);
    }

    #[test]
    fn test_unknown_values() {
        let verifier = AlignmentVerifier::new(vec![]);
        let proof = ZkAlignmentProof {
            values_hash: [0u8; 32],
            decision_digest: [1u8; 32],
            proof_blob: vec![0u8; 64],
            public_inputs: vec![],
        };
        assert_eq!(verifier.verify(&proof), AlignmentVerdict::Misaligned("Unknown values document".into()));
    }

    #[test]
    fn test_empty_proof() {
        let values = b"test-values";
        let vh = hash_values_document(values);
        let verifier = AlignmentVerifier::new(vec![vh]);
        let proof = ZkAlignmentProof {
            values_hash: vh,
            decision_digest: [1u8; 32],
            proof_blob: vec![],
            public_inputs: vec![],
        };
        assert_eq!(verifier.verify(&proof), AlignmentVerdict::InvalidProof);
    }

    #[test]
    fn test_hash_determinism() {
        let doc = b"sovereign-values-charter";
        let h1 = hash_values_document(doc);
        let h2 = hash_values_document(doc);
        assert_eq!(h1, h2);
    }
}
