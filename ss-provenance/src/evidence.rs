use crate::ProvenanceChain;
use serde::{Deserialize, Serialize};
use ss_core::{SovereignUri, Timestamp};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidencePackage {
    pub package_id: String,
    pub generated_at: Timestamp,
    pub generated_by: SovereignUri,
    pub conformance_profile: String,
    pub target_object: SovereignUri,
    pub chain: ProvenanceChain,
    pub metadata: HashMap<String, String>,
    pub signature: Option<String>,
}

impl EvidencePackage {
    pub fn new(
        generated_by: SovereignUri,
        target_object: SovereignUri,
        chain: ProvenanceChain,
        conformance_profile: String,
    ) -> Self {
        Self {
            package_id: format!("evidence-{}", uuid::Uuid::new_v4()),
            generated_at: Timestamp::now(),
            generated_by,
            conformance_profile,
            target_object,
            chain,
            metadata: HashMap::new(),
            signature: None,
        }
    }
}
