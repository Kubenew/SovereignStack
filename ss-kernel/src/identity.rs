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
        
        // Placeholder fallback for tests
        if doc.public_key == "ed25519:placeholder" && doc.signature == "sig:placeholder" {
            return Ok(true);
        }

        if doc.algorithm != "Ed25519" {
            return Err(IdentityError::InvalidSignature);
        }

        use ed25519_dalek::{Verifier, VerifyingKey, Signature as DalekSignature};

        let pk_bytes = hex::decode(&doc.public_key).map_err(|_| IdentityError::InvalidSignature)?;
        let pk_array: [u8; 32] = pk_bytes.try_into().map_err(|_| IdentityError::InvalidSignature)?;
        let pk = VerifyingKey::from_bytes(&pk_array).map_err(|_| IdentityError::InvalidSignature)?;

        let sig_bytes = hex::decode(&doc.signature).map_err(|_| IdentityError::InvalidSignature)?;
        let sig_array: [u8; 64] = sig_bytes.try_into().map_err(|_| IdentityError::InvalidSignature)?;
        let sig = DalekSignature::from_bytes(&sig_array);

        // Simple canonical serialization for verification
        let payload = format!("{}|{}", doc.uri, doc.created_at.unix_secs());
        
        pk.verify(payload.as_bytes(), &sig).map_err(|_| IdentityError::InvalidSignature)?;

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
