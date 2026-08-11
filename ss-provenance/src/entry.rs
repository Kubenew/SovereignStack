use serde::{Deserialize, Serialize};
use ss_core::{SovereignUri, Timestamp};
use ss_crypto::hash::ContentHash;
use ss_crypto::keys::KeyPair;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProvenanceAction {
    Created,
    Modified,
    Delegated,
    Evaluated,
    Executed,
    Revoked,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceEntry {
    pub action: ProvenanceAction,
    pub actor_uri: SovereignUri,
    pub object_uri: SovereignUri,
    pub timestamp: Timestamp,
    pub parent_hash: Option<String>,
    pub content_hash: String,
    pub signature: Option<String>,
}

impl ProvenanceEntry {
    pub fn new(
        action: ProvenanceAction,
        actor_uri: SovereignUri,
        object_uri: SovereignUri,
        parent_hash: Option<String>,
        payload: &serde_json::Value,
    ) -> Self {
        let timestamp = Timestamp::now();
        
        // Canonicalize payload for hashing
        let payload_str = serde_json::to_string(payload).unwrap_or_default();
        let content_hash = ContentHash::compute(payload_str.as_bytes()).as_hex().to_string();

        Self {
            action,
            actor_uri,
            object_uri,
            timestamp,
            parent_hash,
            content_hash,
            signature: None,
        }
    }

    pub fn canonical_bytes(&self) -> Vec<u8> {
        let mut parts = vec![
            serde_json::to_string(&self.action).unwrap_or_default(),
            self.actor_uri.to_string(),
            self.object_uri.to_string(),
            self.timestamp.unix_secs().to_string(),
            self.content_hash.clone(),
        ];
        if let Some(ref ph) = self.parent_hash {
            parts.push(ph.clone());
        }
        parts.join("|").into_bytes()
    }

    pub fn sign(&mut self, keypair: &KeyPair) {
        let bytes = self.canonical_bytes();
        use ed25519_dalek::Signer;
        let sig = keypair.signing_key().sign(&bytes);
        self.signature = Some(hex::encode(sig.to_bytes()));
    }
    
    pub fn hash(&self) -> String {
        let bytes = self.canonical_bytes();
        ContentHash::compute(&bytes).as_hex().to_string()
    }
}
