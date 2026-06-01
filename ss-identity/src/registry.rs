//! Identity registry — local store of known identities with DID resolution.

use std::collections::HashMap;

use ss_core::uri::SovereignUri;

use crate::identity::{AgentIdentity, IdentityDocument};

/// A local registry of known identities with DID resolution.
pub struct IdentityRegistry {
    local_identities: HashMap<String, AgentIdentity>,
    known_identities: HashMap<String, IdentityDocument>,
}

impl IdentityRegistry {
    pub fn new() -> Self {
        Self {
            local_identities: HashMap::new(),
            known_identities: HashMap::new(),
        }
    }

    /// Register a locally-owned identity.
    pub fn register_local(&mut self, identity: AgentIdentity) {
        let key = identity.uri().to_string();
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

    /// Resolve a DID document by URI (returns JSON-LD DID Document).
    pub fn resolve_did(&self, uri: &SovereignUri) -> Option<serde_json::Value> {
        self.known_identities.get(&uri.to_string()).map(|doc| {
            let vm_list: Vec<serde_json::Value> = doc.verification_methods.iter().map(|vm| {
                serde_json::json!({
                    "id": vm.id,
                    "type": "Ed25519VerificationKey2018",
                    "controller": doc.uri.to_string(),
                    "publicKeyMultibase": vm.public_key_multibase,
                })
            }).collect();

            let auth_list: Vec<String> = doc.verification_methods.iter().map(|vm| vm.id.clone()).collect();

            serde_json::json!({
                "@context": [
                    "https://www.w3.org/ns/did/v1",
                    "https://w3id.org/security/suites/ed25519-2018/v1"
                ],
                "id": doc.uri.to_string(),
                "alsoKnownAs": [doc.name.clone()],
                "verificationMethod": vm_list,
                "authentication": auth_list,
                "assertionMethod": auth_list,
                "service": doc.service_endpoints.iter().map(|se| {
                    serde_json::json!({
                        "id": se.id,
                        "type": se.service_type,
                        "serviceEndpoint": se.endpoint,
                    })
                }).collect::<Vec<_>>(),
            })
        })
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

    /// Verify that a public key is or was ever valid for a given identity.
    pub fn verify_key_for_identity(&self, uri: &SovereignUri, key: &ss_crypto::PublicKey) -> bool {
        self.known_identities.get(&uri.to_string()).map_or(false, |doc| {
            &doc.public_key == key
                || doc.key_history.iter().any(|alias| &alias.public_key == key)
        })
    }

    /// Get key history for an identity.
    pub fn key_history(&self, uri: &SovereignUri) -> Vec<&crate::identity::KeyAlias> {
        self.known_identities.get(&uri.to_string()).map_or_else(Vec::new, |doc| {
            doc.key_history.iter().collect()
        })
    }

    pub fn len(&self) -> usize {
        self.known_identities.len()
    }

    pub fn is_empty(&self) -> bool {
        self.known_identities.is_empty()
    }

    pub fn local_count(&self) -> usize {
        self.local_identities.len()
    }

    pub fn remove(&mut self, uri: &SovereignUri) -> bool {
        let key = uri.to_string();
        self.local_identities.remove(&key);
        self.known_identities.remove(&key).is_some()
    }

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
    use ss_crypto::PublicKey as CryptoPubKey;

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
    fn resolve_did_document() {
        let mut registry = IdentityRegistry::new();
        let identity = AgentIdentity::create("did-resolve", IdentityType::Agent);
        let uri = identity.uri().clone();
        registry.register_local(identity);
        let doc = registry.resolve_did(&uri);
        assert!(doc.is_some());
        let did = doc.unwrap();
        assert_eq!(did["id"], "agent://did-resolve");
        assert!(did["verificationMethod"].as_array().unwrap().len() >= 1);
        assert!(did["@context"].as_array().unwrap().len() >= 1);
    }

    #[test]
    fn verify_key_for_identity_local() {
        let mut registry = IdentityRegistry::new();
        let identity = AgentIdentity::create("key-test", IdentityType::Agent);
        let uri = identity.uri().clone();
        let pk = identity.public_key().clone();
        registry.register_local(identity);
        assert!(registry.verify_key_for_identity(&uri, &pk));
    }

    #[test]
    fn verify_key_after_rotation() {
        let mut registry = IdentityRegistry::new();
        let mut identity = AgentIdentity::create("rotate-test", IdentityType::Agent);
        let old_key = identity.public_key().clone();
        identity.rotate_key("scheduled rotation");
        let uri = identity.uri().clone();
        let new_key = identity.public_key().clone();
        registry.register_local(identity);
        assert!(registry.verify_key_for_identity(&uri, &old_key));
        assert!(registry.verify_key_for_identity(&uri, &new_key));
    }

    #[test]
    fn key_history_access() {
        let mut registry = IdentityRegistry::new();
        let mut identity = AgentIdentity::create("hist-test", IdentityType::Agent);
        let pk = identity.public_key().clone();
        identity.rotate_key("test rotation");
        let uri = identity.uri().clone();
        registry.register_local(identity);
        let hist = registry.key_history(&uri);
        assert_eq!(hist.len(), 1);
        assert_eq!(&hist[0].public_key, &pk);
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
