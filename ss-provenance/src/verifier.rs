use crate::{ProvenanceChain, ProvenanceError};
use ed25519_dalek::{Signature as DalekSignature, Verifier, VerifyingKey};

pub struct ChainVerifier;

impl ChainVerifier {
    pub fn verify(
        chain: &ProvenanceChain,
        resolve_key: impl Fn(&ss_core::SovereignUri) -> Option<String>,
    ) -> Result<bool, ProvenanceError> {
        if chain.is_empty() {
            return Err(ProvenanceError::EmptyChain);
        }

        let mut expected_parent = None;

        for entry in &chain.entries {
            // 1. Verify Linkage
            if entry.parent_hash != expected_parent {
                return Err(ProvenanceError::BrokenLink {
                    expected: expected_parent.unwrap_or_else(|| "None".to_string()),
                    found: entry.parent_hash.clone().unwrap_or_else(|| "None".to_string()),
                });
            }

            // 2. Verify Signature
            if let Some(ref sig_hex) = entry.signature {
                let pk_hex = resolve_key(&entry.actor_uri).ok_or_else(|| {
                    ProvenanceError::Crypto(format!("Unknown key for actor {}", entry.actor_uri))
                })?;

                let pk_bytes = hex::decode(&pk_hex)
                    .map_err(|_| ProvenanceError::Crypto("Invalid PK hex".into()))?;
                let pk_array: [u8; 32] = pk_bytes
                    .try_into()
                    .map_err(|_| ProvenanceError::Crypto("Invalid PK length".into()))?;
                let pk = VerifyingKey::from_bytes(&pk_array)
                    .map_err(|_| ProvenanceError::InvalidSignature)?;

                let sig_bytes = hex::decode(sig_hex)
                    .map_err(|_| ProvenanceError::Crypto("Invalid sig hex".into()))?;
                let sig_array: [u8; 64] = sig_bytes
                    .try_into()
                    .map_err(|_| ProvenanceError::Crypto("Invalid sig length".into()))?;
                let sig = DalekSignature::from_bytes(&sig_array);

                let bytes = entry.canonical_bytes();
                pk.verify(&bytes, &sig)
                    .map_err(|_| ProvenanceError::InvalidSignature)?;
            } else {
                return Err(ProvenanceError::InvalidSignature); // Unsigned entries not allowed in verified chain
            }

            expected_parent = Some(entry.hash());
        }

        // 3. Verify root hash matches last entry
        if let Some(last) = chain.entries.last() {
            if chain.root_hash != Some(last.hash()) {
                return Err(ProvenanceError::TamperedEntry);
            }
        }

        Ok(true)
    }
}
