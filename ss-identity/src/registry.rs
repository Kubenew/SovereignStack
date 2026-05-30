//! Identity registry — local store of known identities.

use std::collections::HashMap;

use ss_core::uri::SovereignUri;

use crate::identity::{AgentIdentity, IdentityDocument};

/// A local registry of known identities.
///
/// Each node maintains a registry of identities it has encountered.
/// This is the local component of the Sovereign Identity Graph (SIG).
pub struct IdentityRegistry {
    /// Identities owned by this node (with signing keys).
    local_identities: HashMap<String, AgentIdentity>,
    /// Remote identities discovered through the network.
    known_identities: HashMap<String, IdentityDocument>,
}

impl IdentityRegistry {
    /// Create a new empty registry.
    pub fn new() -> Self {
        Self {
            local_identities: HashMap::new(),
            known_identities: HashMap::new(),
        }
    }

    /// Register a locally-owned identity.
    pub fn register_local(&mut self, identity: AgentIdentity) {
        let key = identity.uri().to_string();
        // Also publish as known
        self.known_identities
            .insert(key.clone(), identity.to_identity_document());
        self.local_identities.insert(key, identity);
    }

    /// Register a remote identity discovered from the network.
    pub fn register_remote(&mut self, document: IdentityDocument) {
        let key = document.uri.to_string();
        self.known_identities.insert(key, document);
    }

    /// Look up an identity by URI.
    pub fn lookup(&self, uri: &SovereignUri) -> Option<&IdentityDocument> {
        self.known_identities.get(&uri.to_string())
    }

    /// Look up a local identity by URI (with signing capability).
    pub fn lookup_local(&self, uri: &SovereignUri) -> Option<&AgentIdentity> {
        self.local_identities.get(&uri.to_string())
    }

    /// Find identities that have a specific capability.
    pub fn find_by_capability(&self, capability: &str) -> Vec<&IdentityDocument> {
        self.known_identities
            .values()
            .filter(|doc| doc.capabilities.iter().any(|c| c == capability))
            .collect()
    }

    /// Find all active identities.
    pub fn active_identities(&self) -> Vec<&IdentityDocument> {
        self.known_identities
            .values()
            .filter(|doc| doc.active)
            .collect()
    }

    /// Returns the number of known identities.
    pub fn len(&self) -> usize {
        self.known_identities.len()
    }

    /// Returns true if the registry is empty.
    pub fn is_empty(&self) -> bool {
        self.known_identities.is_empty()
    }

    /// Returns the number of locally-owned identities.
    pub fn local_count(&self) -> usize {
        self.local_identities.len()
    }

    /// Remove an identity from the registry.
    pub fn remove(&mut self, uri: &SovereignUri) -> bool {
        let key = uri.to_string();
        self.local_identities.remove(&key);
        self.known_identities.remove(&key).is_some()
    }

    /// List all known identity URIs.
    pub fn list_uris(&self) -> Vec<&str> {
        self.known_identities.keys().map(|k| k.as_str()).collect()
    }
}

impl Default for IdentityRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::identity::IdentityType;

    #[test]
    fn register_and_lookup() {
        let mut registry = IdentityRegistry::new();
        let identity = AgentIdentity::create("test-agent", IdentityType::Agent);
        let uri = identity.uri().clone();

        registry.register_local(identity);
        assert_eq!(registry.len(), 1);
        assert!(registry.lookup(&uri).is_some());
        assert!(registry.lookup_local(&uri).is_some());
    }

    #[test]
    fn find_by_capability() {
        let mut registry = IdentityRegistry::new();

        let agent1 = AgentIdentity::create("legal-agent", IdentityType::Agent)
            .with_capabilities(vec!["legal_review".to_string()]);
        let agent2 = AgentIdentity::create("code-agent", IdentityType::Agent)
            .with_capabilities(vec!["coding".to_string()]);
        let agent3 = AgentIdentity::create("multi-agent", IdentityType::Agent)
            .with_capabilities(vec!["legal_review".to_string(), "coding".to_string()]);

        registry.register_local(agent1);
        registry.register_local(agent2);
        registry.register_local(agent3);

        let legal = registry.find_by_capability("legal_review");
        assert_eq!(legal.len(), 2);

        let coding = registry.find_by_capability("coding");
        assert_eq!(coding.len(), 2);

        let unknown = registry.find_by_capability("unknown");
        assert_eq!(unknown.len(), 0);
    }

    #[test]
    fn remove_identity() {
        let mut registry = IdentityRegistry::new();
        let identity = AgentIdentity::create("removable", IdentityType::Agent);
        let uri = identity.uri().clone();

        registry.register_local(identity);
        assert_eq!(registry.len(), 1);

        assert!(registry.remove(&uri));
        assert_eq!(registry.len(), 0);
        assert!(registry.lookup(&uri).is_none());
    }
}
