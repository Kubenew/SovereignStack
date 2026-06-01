//! Agent identity types, key rotation, and DID document compliance.

use serde::{Deserialize, Serialize};
use std::fmt;

use ss_core::timestamp::Timestamp;
use ss_core::uri::{SovereignUri, UriScheme};
use ss_core::types::Jurisdiction;
use ss_crypto::keys::{KeyPair, PublicKey};

/// The type of identity in the network.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IdentityType {
    Agent,
    Organization,
    Robot,
    Node,
    Human,
    Service,
}

impl IdentityType {
    pub fn uri_scheme(&self) -> UriScheme {
        match self {
            Self::Agent | Self::Human | Self::Service => UriScheme::Agent,
            Self::Organization => UriScheme::Org,
            Self::Robot => UriScheme::Robot,
            Self::Node => UriScheme::Node,
        }
    }
}

/// Verification method type per DID Core specification.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum VerificationMethodType {
    Ed25519VerificationKey2018,
    Ed25519VerificationKey2020,
    JsonWebKey2020,
    Multikey,
}

/// A verification method entry for DID documents.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationMethod {
    pub id: String,
    pub method_type: VerificationMethodType,
    pub public_key_multibase: Option<String>,
    pub public_key_jwk: Option<serde_json::Value>,
}

/// A service endpoint for DID documents.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceEndpoint {
    pub id: String,
    pub service_type: String,
    pub endpoint: String,
    pub description: Option<String>,
}

/// A historical key alias used in key rotation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyAlias {
    pub alias_id: String,
    pub public_key: PublicKey,
    pub valid_from: Timestamp,
    pub valid_until: Option<Timestamp>,
    pub reason: String,
}

/// An agent's identity in the Sovereign Intelligence Network.
///
/// Supports key rotation, DID document export, and revocation chain.
#[derive(Debug, Serialize, Deserialize)]
pub struct AgentIdentity {
    uri: SovereignUri,
    name: String,
    identity_type: IdentityType,
    public_key: PublicKey,
    capabilities: Vec<String>,
    created_at: Timestamp,
    jurisdiction: Option<Jurisdiction>,
    active: bool,
    /// Key rotation history (previous public keys with validity windows).
    key_history: Vec<KeyAlias>,
    /// Verification methods for DID document compliance.
    verification_methods: Vec<VerificationMethod>,
    /// Service endpoints for DID document.
    service_endpoints: Vec<ServiceEndpoint>,
    #[serde(skip)]
    keypair: Option<KeyPair>,
}

impl AgentIdentity {
    pub fn create(name: &str, identity_type: IdentityType) -> Self {
        let keypair = KeyPair::generate();
        let public_key = keypair.public_key();
        let uri = SovereignUri::new(identity_type.uri_scheme(), name);

        let mut methods = Vec::new();
        methods.push(VerificationMethod {
            id: format!("{}#key-1", uri),
            method_type: VerificationMethodType::Ed25519VerificationKey2018,
            public_key_multibase: Some(format!("z{}", public_key.to_hex())),
            public_key_jwk: None,
        });

        Self {
            uri,
            name: name.to_string(),
            identity_type,
            public_key,
            capabilities: Vec::new(),
            created_at: Timestamp::now(),
            jurisdiction: None,
            active: true,
            key_history: Vec::new(),
            verification_methods: methods,
            service_endpoints: Vec::new(),
            keypair: Some(keypair),
        }
    }

    pub fn from_public_key(
        name: &str,
        identity_type: IdentityType,
        public_key: PublicKey,
    ) -> Self {
        let uri = SovereignUri::new(identity_type.uri_scheme(), name);

        let mut methods = Vec::new();
        methods.push(VerificationMethod {
            id: format!("{}#key-1", uri),
            method_type: VerificationMethodType::Ed25519VerificationKey2018,
            public_key_multibase: Some(format!("z{}", public_key.to_hex())),
            public_key_jwk: None,
        });

        Self {
            uri,
            name: name.to_string(),
            identity_type,
            public_key,
            capabilities: Vec::new(),
            created_at: Timestamp::now(),
            jurisdiction: None,
            active: true,
            key_history: Vec::new(),
            verification_methods: methods,
            service_endpoints: Vec::new(),
            keypair: None,
        }
    }

    pub fn with_capabilities(mut self, capabilities: Vec<String>) -> Self {
        self.capabilities = capabilities;
        self
    }

    pub fn with_jurisdiction(mut self, jurisdiction: Jurisdiction) -> Self {
        self.jurisdiction = Some(jurisdiction);
        self
    }

    pub fn with_service_endpoint(mut self, endpoint: ServiceEndpoint) -> Self {
        self.service_endpoints.push(endpoint);
        self
    }

    /// Rotate the identity's key pair, recording the previous key in history.
    pub fn rotate_key(&mut self, reason: &str) {
        let old_key = self.public_key.clone();
        let alias = KeyAlias {
            alias_id: format!("{:#key-{}", self.uri, self.key_history.len() + 1),
            public_key: old_key,
            valid_from: self.created_at,
            valid_until: Some(Timestamp::now()),
            reason: reason.to_string(),
        };
        self.key_history.push(alias);

        let new_kp = KeyPair::generate();
        self.public_key = new_kp.public_key();
        self.keypair = Some(new_kp);

        self.verification_methods.push(VerificationMethod {
            id: format!("{}#key-{}", self.uri, self.key_history.len() + 1),
            method_type: VerificationMethodType::Ed25519VerificationKey2018,
            public_key_multibase: Some(format!("z{}", self.public_key.to_hex())),
            public_key_jwk: None,
        });
    }

    /// Returns the key rotation history.
    pub fn key_history(&self) -> &[KeyAlias] {
        &self.key_history
    }

    /// Returns verification methods.
    pub fn verification_methods(&self) -> &[VerificationMethod] {
        &self.verification_methods
    }

    /// Returns service endpoints.
    pub fn service_endpoints(&self) -> &[ServiceEndpoint] {
        &self.service_endpoints
    }

    /// Verify that a given public key was ever valid for this identity.
    pub fn was_valid_key(&self, key: &PublicKey) -> bool {
        &self.public_key == key || self.key_history.iter().any(|a| &a.public_key == key)
    }

    pub fn uri(&self) -> &SovereignUri {
        &self.uri
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn identity_type(&self) -> IdentityType {
        self.identity_type
    }

    pub fn public_key(&self) -> &PublicKey {
        &self.public_key
    }

    pub fn capabilities(&self) -> &[String] {
        &self.capabilities
    }

    pub fn jurisdiction(&self) -> Option<&Jurisdiction> {
        self.jurisdiction.as_ref()
    }

    pub fn is_active(&self) -> bool {
        self.active
    }

    pub fn deactivate(&mut self) {
        self.active = false;
    }

    pub fn sign(&self, payload: &[u8]) -> Option<ss_crypto::Signature> {
        self.keypair
            .as_ref()
            .map(|kp| ss_crypto::Signature::sign(kp, payload))
    }

    pub fn has_capability(&self, capability: &str) -> bool {
        self.capabilities.iter().any(|c| c == capability)
    }

    /// Export as a DID-compliant identity document.
    pub fn to_identity_document(&self) -> IdentityDocument {
        IdentityDocument {
            uri: self.uri.clone(),
            name: self.name.clone(),
            identity_type: self.identity_type,
            public_key: self.public_key.clone(),
            capabilities: self.capabilities.clone(),
            created_at: self.created_at,
            jurisdiction: self.jurisdiction.clone(),
            active: self.active,
            verification_methods: self.verification_methods.clone(),
            key_history: self.key_history.clone(),
            service_endpoints: self.service_endpoints.clone(),
        }
    }

    /// Export as a DID JSON document (DID Core compliant subset).
    pub fn to_did_document(&self) -> serde_json::Value {
        serde_json::json!({
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/ed25519-2018/v1"
            ],
            "id": self.uri.to_string(),
            "verificationMethod": self.verification_methods.iter().map(|vm| {
                serde_json::json!({
                    "id": vm.id,
                    "type": match vm.method_type {
                        VerificationMethodType::Ed25519VerificationKey2018 => "Ed25519VerificationKey2018",
                        VerificationMethodType::Ed25519VerificationKey2020 => "Ed25519VerificationKey2020",
                        VerificationMethodType::JsonWebKey2020 => "JsonWebKey2020",
                        VerificationMethodType::Multikey => "Multikey",
                    },
                    "controller": self.uri.to_string(),
                    "publicKeyMultibase": vm.public_key_multibase,
                })
            }).collect::<Vec<_>>(),
            "authentication": self.verification_methods.iter().map(|vm| vm.id.clone()).collect::<Vec<_>>(),
            "assertionMethod": self.verification_methods.iter().map(|vm| vm.id.clone()).collect::<Vec<_>>(),
            "service": self.service_endpoints.iter().map(|se| {
                serde_json::json!({
                    "id": se.id,
                    "type": se.service_type,
                    "serviceEndpoint": se.endpoint,
                })
            }).collect::<Vec<_>>(),
        })
    }
}

impl fmt::Display for AgentIdentity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{} ({:?}) [{}]",
            self.uri, self.identity_type, self.public_key
        )
    }
}

/// A shareable identity document with DID support.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentityDocument {
    pub uri: SovereignUri,
    pub name: String,
    pub identity_type: IdentityType,
    pub public_key: PublicKey,
    pub capabilities: Vec<String>,
    pub created_at: Timestamp,
    pub jurisdiction: Option<Jurisdiction>,
    pub active: bool,
    pub verification_methods: Vec<VerificationMethod>,
    pub key_history: Vec<KeyAlias>,
    pub service_endpoints: Vec<ServiceEndpoint>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_agent_identity() {
        let id = AgentIdentity::create("researcher-1", IdentityType::Agent);
        assert_eq!(id.name(), "researcher-1");
        assert_eq!(id.identity_type(), IdentityType::Agent);
        assert!(id.is_active());
        assert_eq!(id.uri().scheme(), UriScheme::Agent);
        assert_eq!(id.uri().authority(), "researcher-1");
    }

    #[test]
    fn identity_with_capabilities() {
        let id = AgentIdentity::create("legal-agent", IdentityType::Agent)
            .with_capabilities(vec![
                "legal_review".to_string(),
                "contract_analysis".to_string(),
            ]);
        assert!(id.has_capability("legal_review"));
        assert!(id.has_capability("contract_analysis"));
        assert!(!id.has_capability("coding"));
    }

    #[test]
    fn identity_signing() {
        let id = AgentIdentity::create("signer", IdentityType::Agent);
        let payload = b"important data";
        let sig = id.sign(payload).expect("should be able to sign");
        assert!(sig.verify(payload));
    }

    #[test]
    fn identity_deactivation() {
        let mut id = AgentIdentity::create("temp", IdentityType::Agent);
        assert!(id.is_active());
        id.deactivate();
        assert!(!id.is_active());
    }

    #[test]
    fn identity_document_export() {
        let id = AgentIdentity::create("test", IdentityType::Agent)
            .with_capabilities(vec!["analysis".to_string()]);
        let doc = id.to_identity_document();
        assert_eq!(doc.name, "test");
        assert_eq!(doc.capabilities, vec!["analysis"]);
        let json = serde_json::to_string(&doc).unwrap();
        assert!(json.contains("test"));
    }

    #[test]
    fn key_rotation_tracks_history() {
        let mut id = AgentIdentity::create("rotatable", IdentityType::Agent);
        let first_key = id.public_key().clone();

        id.rotate_key("scheduled rotation");
        assert!(id.key_history().len() == 1);
        assert_ne!(id.public_key().to_hex(), first_key.to_hex());
        assert!(id.was_valid_key(&first_key));
        assert!(id.was_valid_key(id.public_key()));
    }

    #[test]
    fn multiple_rotations() {
        let mut id = AgentIdentity::create("multi-rot", IdentityType::Agent);
        let key0 = id.public_key().clone();
        id.rotate_key("first rotation");
        let key1 = id.public_key().clone();
        id.rotate_key("second rotation");

        assert_eq!(id.key_history().len(), 2);
        assert!(id.was_valid_key(&key0));
        assert!(id.was_valid_key(&key1));
        assert!(id.was_valid_key(id.public_key()));
    }

    #[test]
    fn did_document_format() {
        let id = AgentIdentity::create("did-test", IdentityType::Agent);
        let doc = id.to_did_document();
        assert_eq!(doc["id"], "agent://did-test");
        assert!(doc["verificationMethod"].as_array().unwrap().len() >= 1);
        assert!(doc["authentication"].as_array().unwrap().len() >= 1);
    }

    #[test]
    fn did_document_with_service_endpoint() {
        let id = AgentIdentity::create("svc-test", IdentityType::Agent)
            .with_service_endpoint(ServiceEndpoint {
                id: "agent://svc-test#api".into(),
                service_type: "SovereignStackAPI".into(),
                endpoint: "https://api.svc-test.agent".into(),
                description: Some("Main API endpoint".into()),
            });
        let doc = id.to_did_document();
        let services = doc["service"].as_array().unwrap();
        assert_eq!(services.len(), 1);
        assert_eq!(services[0]["serviceEndpoint"], "https://api.svc-test.agent");
    }

    #[test]
    fn verification_methods_in_document() {
        let mut id = AgentIdentity::create("vm-test", IdentityType::Agent);
        let methods_before = id.verification_methods().len();
        id.rotate_key("rotation adds new verification method");
        assert_eq!(id.verification_methods().len(), methods_before + 1);
    }

    #[test]
    fn organization_identity() {
        let id = AgentIdentity::create("acme", IdentityType::Organization);
        assert_eq!(id.uri().scheme(), UriScheme::Org);
    }

    #[test]
    fn robot_identity() {
        let id = AgentIdentity::create("drone-12", IdentityType::Robot);
        assert_eq!(id.uri().scheme(), UriScheme::Robot);
    }
}
