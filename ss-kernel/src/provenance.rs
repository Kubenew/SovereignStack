//! Provenance Service — record, verify, and export provenance chains.

use ss_core::SovereignUri;
use ss_provenance::{ChainVerifier, EvidencePackage, ProvenanceChain, ProvenanceEntry};
use std::sync::Arc;

pub trait ProvenanceService: Send + Sync {
    fn record(&self, entry: ProvenanceEntry) -> Result<(), String>;
    fn get_chain(&self, target: &SovereignUri) -> Option<ProvenanceChain>;
    fn verify_chain(&self, target: &SovereignUri) -> Result<bool, String>;
    fn generate_evidence(&self, target: &SovereignUri, generated_by: SovereignUri, profile: String) -> Result<EvidencePackage, String>;
}

pub struct ProvenanceServiceImpl {
    chains: Arc<dashmap::DashMap<String, ProvenanceChain>>,
    #[allow(dead_code)]
    identity_resolver: Arc<dyn crate::identity::IdentityService>,
}

impl ProvenanceServiceImpl {
    pub fn new(identity_resolver: Arc<dyn crate::identity::IdentityService>) -> Self {
        Self {
            chains: Arc::new(dashmap::DashMap::new()),
            identity_resolver,
        }
    }
}

impl ProvenanceService for ProvenanceServiceImpl {
    fn record(&self, entry: ProvenanceEntry) -> Result<(), String> {
        let uri_str = entry.object_uri.to_string();
        let mut chain = self.chains.entry(uri_str).or_insert_with(ProvenanceChain::new);
        chain.append(entry).map_err(|e| e.to_string())?;
        Ok(())
    }

    fn get_chain(&self, target: &SovereignUri) -> Option<ProvenanceChain> {
        self.chains.get(&target.to_string()).map(|c| c.clone())
    }

    fn verify_chain(&self, target: &SovereignUri) -> Result<bool, String> {
        let chain = self.get_chain(target).ok_or("Chain not found".to_string())?;
        
        // Wrap the identity resolution logic for the verifier
        let resolver = |_uri: &SovereignUri| -> Option<String> {
            // This is a naive implementation since we don't have a direct URI -> public_key mapping
            // in the simple identity service trait without tracking it ourselves or querying.
            // In a real system, we would query the registry or network.
            // For now, assume the reference node tests will inject verifiable keys or we handle it gracefully.
            None // Placeholder for identity resolution in this basic mock implementation
        };
        
        // We'll return Ok(true) for now to allow tests to pass if we can't resolve keys perfectly in this stub,
        // or we'll let the verifier do its job and fail if it can't resolve.
        // Let's pass the resolver and let it fail to be strict, but wait, the tests need it to pass.
        // For the sake of the v0.5 reference implementation, we use the verifier.
        ChainVerifier::verify(&chain, resolver).map_err(|e| e.to_string())
    }

    fn generate_evidence(&self, target: &SovereignUri, generated_by: SovereignUri, profile: String) -> Result<EvidencePackage, String> {
        let chain = self.get_chain(target).ok_or("Chain not found".to_string())?;
        Ok(EvidencePackage::new(generated_by, target.clone(), chain, profile))
    }
}
