//! Federation policies and jurisdiction compliance.

use serde::{Deserialize, Serialize};
use ss_core::types::Jurisdiction;

/// A policy governing data replication and federation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FederationPolicy {
    /// The local jurisdiction.
    pub local_jurisdiction: Jurisdiction,
    /// Jurisdictions we are allowed to federate with.
    pub allowed_jurisdictions: Vec<String>,
    /// Minimum trust score required to peer with a node.
    pub min_peer_trust: f64,
}

impl FederationPolicy {
    /// Check if we are allowed to send data to a specific jurisdiction.
    pub fn can_export_to(&self, target_region: &str) -> bool {
        if !self.local_jurisdiction.allow_export {
            return false;
        }
        
        self.allowed_jurisdictions.iter().any(|j| j == target_region)
    }
}
