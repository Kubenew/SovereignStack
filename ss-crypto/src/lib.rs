//! # ss-crypto
//!
//! Cryptographic primitives for SovereignStack:
//!
//! - **Ed25519 keypairs** — agent identity signing and verification
//! - **Content hashing** — SHA-256 for content-addressed storage
//! - **Signatures** — sign and verify arbitrary payloads
//!
//! Every agent in SovereignStack has a cryptographic identity based on
//! Ed25519 public key pairs, enabling trust, verification, and reputation
//! across the sovereign intelligence network.

pub mod keys;
pub mod hash;
pub mod signature;

pub use keys::{KeyPair, PublicKey};
pub use hash::ContentHash;
pub use signature::Signature;
