//! Ed25519 key pair management for agent identities.

use ed25519_dalek::{SigningKey, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};

/// An Ed25519 key pair for agent identity.
///
/// Every agent in SovereignStack has a persistent cryptographic identity.
/// The public key is shared across the network; the signing key is kept private.
#[derive(Clone)]
pub struct KeyPair {
    signing_key: SigningKey,
}

impl std::fmt::Debug for KeyPair {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("KeyPair")
            .field("signing_key", &"<REDACTED>")
            .finish()
    }
}

impl KeyPair {
    /// Generate a new random key pair.
    pub fn generate() -> Self {
        let signing_key = SigningKey::generate(&mut OsRng);
        Self { signing_key }
    }

    /// Create from an existing signing key bytes (32 bytes).
    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        let signing_key = SigningKey::from_bytes(bytes);
        Self { signing_key }
    }

    /// Returns the public key.
    pub fn public_key(&self) -> PublicKey {
        PublicKey(self.signing_key.verifying_key())
    }

    /// Returns reference to the signing key.
    pub fn signing_key(&self) -> &SigningKey {
        &self.signing_key
    }

    /// Returns the signing key bytes.
    pub fn to_bytes(&self) -> [u8; 32] {
        self.signing_key.to_bytes()
    }
}

/// An Ed25519 public key (verifying key).
///
/// This is the shareable part of an agent's identity. It can verify
/// signatures produced by the corresponding signing key.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PublicKey(VerifyingKey);

impl PublicKey {
    /// Create from raw bytes (32 bytes).
    pub fn from_bytes(bytes: &[u8; 32]) -> Result<Self, ed25519_dalek::SignatureError> {
        let vk = VerifyingKey::from_bytes(bytes)?;
        Ok(Self(vk))
    }

    /// Returns the inner verifying key.
    pub fn verifying_key(&self) -> &VerifyingKey {
        &self.0
    }

    /// Returns the key as bytes.
    pub fn to_bytes(&self) -> [u8; 32] {
        self.0.to_bytes()
    }

    /// Returns the key as hex string.
    pub fn to_hex(&self) -> String {
        hex::encode(self.to_bytes())
    }
}

impl Serialize for PublicKey {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_hex())
    }
}

impl<'de> Deserialize<'de> for PublicKey {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let hex_str = String::deserialize(deserializer)?;
        let bytes = hex::decode(&hex_str).map_err(serde::de::Error::custom)?;
        let array: [u8; 32] = bytes
            .try_into()
            .map_err(|_| serde::de::Error::custom("invalid key length"))?;
        PublicKey::from_bytes(&array).map_err(serde::de::Error::custom)
    }
}

impl std::fmt::Display for PublicKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "ed25519:{}", &self.to_hex()[..16])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generate_keypair() {
        let kp = KeyPair::generate();
        let pk = kp.public_key();
        assert_eq!(pk.to_bytes().len(), 32);
    }

    #[test]
    fn keypair_roundtrip() {
        let kp1 = KeyPair::generate();
        let bytes = kp1.to_bytes();
        let kp2 = KeyPair::from_bytes(&bytes);
        assert_eq!(kp1.public_key(), kp2.public_key());
    }

    #[test]
    fn public_key_hex_roundtrip() {
        let kp = KeyPair::generate();
        let pk = kp.public_key();
        let hex_str = pk.to_hex();
        let bytes = hex::decode(&hex_str).unwrap();
        let array: [u8; 32] = bytes.try_into().unwrap();
        let pk2 = PublicKey::from_bytes(&array).unwrap();
        assert_eq!(pk, pk2);
    }
}
