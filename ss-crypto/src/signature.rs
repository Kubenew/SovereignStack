//! Digital signatures for verifiable objects.

use ed25519_dalek::{Signer, Verifier};
use serde::{Deserialize, Serialize};
use std::fmt;

use crate::keys::{KeyPair, PublicKey};

/// A digital signature over some payload.
///
/// Every artifact, event, and identity attestation in SovereignStack
/// is signed, enabling cryptographic verification across the network.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Signature {
    /// The raw signature bytes (hex-encoded).
    bytes: String,
    /// The public key of the signer.
    signer: PublicKey,
}

impl Signature {
    /// Sign a payload with the given key pair.
    pub fn sign(keypair: &KeyPair, payload: &[u8]) -> Self {
        let sig = keypair.signing_key().sign(payload);
        Self {
            bytes: hex::encode(sig.to_bytes()),
            signer: keypair.public_key(),
        }
    }

    /// Verify this signature against the given payload.
    pub fn verify(&self, payload: &[u8]) -> bool {
        let sig = match self.decode_signature() {
            Some(s) => s,
            None => return false,
        };
        self.signer.verifying_key().verify(payload, &sig).is_ok()
    }

    /// Verify this signature against the given payload using an external public key.
    pub fn verify_with_key(&self, public_key: &PublicKey, payload: &[u8]) -> bool {
        let sig = match self.decode_signature() {
            Some(s) => s,
            None => return false,
        };
        public_key.verifying_key().verify(payload, &sig).is_ok()
    }

    fn decode_signature(&self) -> Option<ed25519_dalek::Signature> {
        let sig_bytes = hex::decode(&self.bytes).ok()?;
        let sig_array: [u8; 64] = sig_bytes.try_into().ok()?;
        Some(ed25519_dalek::Signature::from_bytes(&sig_array))
    }

    /// Returns the signer's public key.
    pub fn signer(&self) -> &PublicKey {
        &self.signer
    }

    /// Returns the signature bytes as hex.
    pub fn as_hex(&self) -> &str {
        &self.bytes
    }
}

impl fmt::Display for Signature {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "sig:{}...", &self.bytes[..16.min(self.bytes.len())])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sign_and_verify() {
        let kp = KeyPair::generate();
        let payload = b"sovereign intelligence";
        let sig = Signature::sign(&kp, payload);
        assert!(sig.verify(payload));
    }

    #[test]
    fn verify_wrong_payload_fails() {
        let kp = KeyPair::generate();
        let sig = Signature::sign(&kp, b"original");
        assert!(!sig.verify(b"tampered"));
    }

    #[test]
    fn verify_with_external_key() {
        let kp1 = KeyPair::generate();
        let kp2 = KeyPair::generate();
        let sig = Signature::sign(&kp1, b"payload");
        assert!(sig.verify_with_key(&kp1.public_key(), b"payload"));
        assert!(!sig.verify_with_key(&kp2.public_key(), b"payload"));
        assert!(!sig.verify_with_key(&kp1.public_key(), b"tampered"));
    }

    #[test]
    fn signature_display() {
        let kp = KeyPair::generate();
        let sig = Signature::sign(&kp, b"test");
        let display = sig.to_string();
        assert!(display.starts_with("sig:"));
    }
}
