//! # ss-provenance
//!
//! Tamper-evident cryptographic provenance chains and evidence generation
//! for SovereignStack.
//!
//! Every action in SovereignStack is recorded in a provenance chain. Each
//! entry is cryptographically linked to the previous entry, creating an
//! immutable audit log.

pub mod chain;
pub mod entry;
pub mod evidence;
pub mod verifier;

pub use chain::ProvenanceChain;
pub use entry::{ProvenanceAction, ProvenanceEntry};
pub use evidence::EvidencePackage;
pub use verifier::ChainVerifier;

#[derive(Debug, thiserror::Error)]
pub enum ProvenanceError {
    #[error("invalid signature")]
    InvalidSignature,
    #[error("invalid hash linkage: expected {expected}, found {found}")]
    BrokenLink { expected: String, found: String },
    #[error("tampered entry: content hash mismatch")]
    TamperedEntry,
    #[error("empty chain")]
    EmptyChain,
    #[error("crypto error: {0}")]
    Crypto(String),
}
