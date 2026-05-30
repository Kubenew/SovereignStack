//! Content hashing for content-addressed storage.
//!
//! Uses SHA-256 to create deterministic hashes of content,
//! forming the basis of the Merkle Memory Tree structure.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt;

/// A SHA-256 content hash.
///
/// Used throughout SovereignStack for content-addressed storage,
/// artifact verification, and Merkle tree construction.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ContentHash(String);

impl ContentHash {
    /// Compute the SHA-256 hash of the given data.
    pub fn compute(data: &[u8]) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(data);
        let result = hasher.finalize();
        Self(hex::encode(result))
    }

    /// Create from an existing hex string.
    pub fn from_hex(hex: impl Into<String>) -> Self {
        Self(hex.into())
    }

    /// Returns the hex representation.
    pub fn as_hex(&self) -> &str {
        &self.0
    }

    /// Returns the short form (first 12 characters).
    pub fn short(&self) -> &str {
        &self.0[..12.min(self.0.len())]
    }

    /// Verify that data matches this hash.
    pub fn verify(&self, data: &[u8]) -> bool {
        let computed = Self::compute(data);
        computed == *self
    }
}

impl fmt::Display for ContentHash {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "sha256:{}", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hash_deterministic() {
        let data = b"hello sovereign world";
        let h1 = ContentHash::compute(data);
        let h2 = ContentHash::compute(data);
        assert_eq!(h1, h2);
    }

    #[test]
    fn hash_different_data() {
        let h1 = ContentHash::compute(b"hello");
        let h2 = ContentHash::compute(b"world");
        assert_ne!(h1, h2);
    }

    #[test]
    fn hash_verify() {
        let data = b"test content";
        let hash = ContentHash::compute(data);
        assert!(hash.verify(data));
        assert!(!hash.verify(b"wrong content"));
    }

    #[test]
    fn hash_display() {
        let hash = ContentHash::compute(b"test");
        let display = hash.to_string();
        assert!(display.starts_with("sha256:"));
    }
}
