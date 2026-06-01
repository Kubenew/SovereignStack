//! Identity Service — key generation, certificate management, verification.

use ss_core::{SovereignUri, Timestamp};
use std::sync::Arc;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct IdentityDocument {
    pub uri: SovereignUri,
    pub public_key: String,
    pub algorithm: String,
    pub created_at: Timestamp,
    pub expires_at: Option<Timestamp>,
    pub metadata: std::collections::HashMap<String, String>,
    pub signature: String,
}

#[derive(Debug, thiserror::Error)]
pub enum IdentityError {
    #[error("invalid signature")]
    InvalidSignature,
    #[error("expired identity")]
    Expired,
    #[error("revoked identity")]
    Revoked,
    #[error("key generation failed: {0}")]
    KeyGeneration(String),
}

pub trait IdentityService: Send + Sync {
    fn generate(&self, uri: &SovereignUri) -> Result<IdentityDocument, IdentityError>;
    fn verify(&self, doc: &IdentityDocument) -> Result<bool, IdentityError>;
    fn revoke(&self, uri: &SovereignUri) -> Result<(), IdentityError>;
    fn is_revoked(&self, uri: &SovereignUri) -> bool;
}

pub struct IdentityServiceImpl {
    store: Arc<dashmap::DashMap<String, IdentityDocument>>,
    revoked: Arc<dashmap::DashSet<String>>,
}

impl IdentityServiceImpl {
    pub fn new() -> Self {
        Self {
            store: Arc::new(dashmap::DashMap::new()),
            revoked: Arc::new(dashmap::DashSet::new()),
        }
    }
}

impl IdentityService for IdentityServiceImpl {
    fn generate(&self, uri: &SovereignUri) -> Result<IdentityDocument, IdentityError> {
        // Placeholder: key generation would use ed25519-dalek
        let doc = IdentityDocument {
            uri: uri.clone(),
            public_key: "ed25519:placeholder".into(),
            algorithm: "Ed25519".into(),
            created_at: Timestamp::now(),
            expires_at: None,
            metadata: std::collections::HashMap::new(),
            signature: "sig:placeholder".into(),
        };
        self.store.insert(uri.to_string(), doc.clone());
        Ok(doc)
    }

    fn verify(&self, doc: &IdentityDocument) -> Result<bool, IdentityError> {
        if self.revoked.contains(&doc.uri.to_string()) {
            return Err(IdentityError::Revoked);
        }
        if let Some(expires) = doc.expires_at {
            if Timestamp::now() > expires {
                return Err(IdentityError::Expired);
            }
        }
        Ok(true)
    }

    fn revoke(&self, uri: &SovereignUri) -> Result<(), IdentityError> {
        self.revoked.insert(uri.to_string());
        Ok(())
    }

    fn is_revoked(&self, uri: &SovereignUri) -> bool {
        self.revoked.contains(&uri.to_string())
    }
}
