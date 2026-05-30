//! Remote Procedure Call definitions for SovereignStack.
//!
//! While the Sovereign Event Bus handles async state replication,
//! some operations (like capability queries and trust verifications)
//! require synchronous Request-Response semantics.

// In a full implementation, these would be generated from .proto files
// using the prost-build crate. For scaffolding, we define the Rust
// structs that map to what the Protobuf definitions would look like.

use serde::{Deserialize, Serialize};

/// Request to query for a capability.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityQueryReq {
    pub required_capability: String,
    pub language: Option<String>,
    pub min_accuracy: Option<f64>,
}

/// Response containing matching capabilities.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityQueryRes {
    pub matches: Vec<CapabilityMatchDto>,
}

/// A matched capability provider.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityMatchDto {
    pub provider_uri: String,
    pub relevance_score: f64,
    pub accuracy: f64,
    pub cost: f64,
}

/// Request to lookup an identity document.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentityLookupReq {
    pub uri: String,
}

/// Response containing an identity document.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentityLookupRes {
    pub document_json: Option<String>, // Serialized IdentityDocument
}
