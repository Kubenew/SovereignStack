//! Agent identity types and creation.

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
    /// An AI agent.
    Agent,
    /// An organization.
    Organization,
    /// A physical robot or device.
    Robot,
    /// A network node.
    Node,
    /// A human user.
    Human,
    /// A service or microservice.
    Service,
}

impl IdentityType {
    /// Returns the corresponding URI scheme.
    pub fn uri_scheme(&self) -> UriScheme {
        match self {
            Self::Agent | Self::Human | Self::Service => UriScheme::Agent,
            Self::Organization => UriScheme::Org,
            Self::Robot => UriScheme::Robot,
            Self::Node => UriScheme::Node,
        }
    }
}

/// An agent's identity in the Sovereign Intelligence Network.
///
/// This is the core identity object that every participant receives.
/// It contains the cryptographic material needed for trust, verification,
/// and reputation across the network.
#[derive(Debug, Serialize, Deserialize)]
pub struct AgentIdentity {
    /// The globally unique URI for this identity.
    uri: SovereignUri,
    /// Human-readable name.
    name: String,
    /// Identity type.
    identity_type: IdentityType,
    /// Ed25519 public key.
    public_key: PublicKey,
    /// Capabilities this identity advertises.
    capabilities: Vec<String>,
    /// When this identity was created.
    created_at: Timestamp,
    /// Optional jurisdiction information.
    jurisdiction: Option<Jurisdiction>,
    /// Whether this identity is currently active.
    active: bool,
    /// The signing key pair (not serialized for security).
    #[serde(skip)]
    keypair: Option<KeyPair>,
}

impl AgentIdentity {
    /// Create a new agent identity with a fresh key pair.
    pub fn create(name: &str, identity_type: IdentityType) -> Self {
        let keypair = KeyPair::generate();
        let public_key = keypair.public_key();
        let uri = SovereignUri::new(identity_type.uri_scheme(), name);

        Self {
            uri,
            name: name.to_string(),
            identity_type,
            public_key,
            capabilities: Vec::new(),
            created_at: Timestamp::now(),
            jurisdiction: None,
            active: true,
            keypair: Some(keypair),
        }
    }

    /// Create an identity from an existing public key (no signing ability).
    pub fn from_public_key(
        name: &str,
        identity_type: IdentityType,
        public_key: PublicKey,
    ) -> Self {
        let uri = SovereignUri::new(identity_type.uri_scheme(), name);

        Self {
            uri,
            name: name.to_string(),
            identity_type,
            public_key,
            capabilities: Vec::new(),
            created_at: Timestamp::now(),
            jurisdiction: None,
            active: true,
            keypair: None,
        }
    }

    /// Add capabilities to this identity.
    pub fn with_capabilities(mut self, capabilities: Vec<String>) -> Self {
        self.capabilities = capabilities;
        self
    }

    /// Set jurisdiction information.
    pub fn with_jurisdiction(mut self, jurisdiction: Jurisdiction) -> Self {
        self.jurisdiction = Some(jurisdiction);
        self
    }

    /// Returns the identity's URI.
    pub fn uri(&self) -> &SovereignUri {
        &self.uri
    }

    /// Returns the identity's name.
    pub fn name(&self) -> &str {
        &self.name
    }

    /// Returns the identity type.
    pub fn identity_type(&self) -> IdentityType {
        self.identity_type
    }

    /// Returns the public key.
    pub fn public_key(&self) -> &PublicKey {
        &self.public_key
    }

    /// Returns the advertised capabilities.
    pub fn capabilities(&self) -> &[String] {
        &self.capabilities
    }

    /// Returns jurisdiction information, if set.
    pub fn jurisdiction(&self) -> Option<&Jurisdiction> {
        self.jurisdiction.as_ref()
    }

    /// Returns whether this identity is active.
    pub fn is_active(&self) -> bool {
        self.active
    }

    /// Deactivate this identity.
    pub fn deactivate(&mut self) {
        self.active = false;
    }

    /// Sign a payload using this identity's key pair.
    ///
    /// Returns `None` if this identity was created from a public key only.
    pub fn sign(&self, payload: &[u8]) -> Option<ss_crypto::Signature> {
        self.keypair
            .as_ref()
            .map(|kp| ss_crypto::Signature::sign(kp, payload))
    }

    /// Check if this identity has a specific capability.
    pub fn has_capability(&self, capability: &str) -> bool {
        self.capabilities.iter().any(|c| c == capability)
    }

    /// Export the identity as a shareable document (without signing key).
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
        }
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

/// A shareable identity document (no private keys).
///
/// This is what gets published to the network for other agents to discover.
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

        // Document should be serializable
        let json = serde_json::to_string(&doc).unwrap();
        assert!(json.contains("test"));
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
