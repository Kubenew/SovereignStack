//! Error types for SovereignStack.

use thiserror::Error;

/// Unified error type for all SovereignStack operations.
#[derive(Debug, Error)]
pub enum Error {
    /// Invalid Sovereign URI format.
    #[error("invalid URI: {0}")]
    InvalidUri(String),

    /// Cryptographic operation failed.
    #[error("crypto error: {0}")]
    Crypto(String),

    /// Identity not found in the network.
    #[error("identity not found: {0}")]
    IdentityNotFound(String),

    /// Capability not available.
    #[error("capability unavailable: {0}")]
    CapabilityUnavailable(String),

    /// Content not found in storage.
    #[error("content not found: {0}")]
    ContentNotFound(String),

    /// Event bus error.
    #[error("event bus error: {0}")]
    EventBus(String),

    /// Federation error.
    #[error("federation error: {0}")]
    Federation(String),

    /// Jurisdiction policy violation.
    #[error("policy violation: {0}")]
    PolicyViolation(String),

    /// Trust threshold not met.
    #[error("insufficient trust: required {required}, got {actual}")]
    InsufficientTrust { required: f64, actual: f64 },

    /// Temporal window expired.
    #[error("object expired at {0}")]
    Expired(String),

    /// Serialization/deserialization error.
    #[error("serialization error: {0}")]
    Serialization(String),

    /// I/O error.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// Generic internal error.
    #[error("internal error: {0}")]
    Internal(String),
}

/// Result type for SovereignStack operations.
pub type Result<T> = std::result::Result<T, Error>;

impl From<serde_json::Error> for Error {
    fn from(e: serde_json::Error) -> Self {
        Error::Serialization(e.to_string())
    }
}
