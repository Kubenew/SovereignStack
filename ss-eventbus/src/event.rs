//! Core event types and structures.

use serde::{Deserialize, Serialize};
use ss_core::timestamp::Timestamp;
use ss_core::types::ObjectId;
use ss_core::uri::SovereignUri;
use ss_crypto::signature::Signature;
use ss_crypto::keys::KeyPair;

/// The type of an event in the system.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EventType {
    /// A new session was created.
    SessionCreated,
    /// A task was started.
    TaskStarted,
    /// A task was completed.
    TaskCompleted,
    /// An artifact was published to CAS.
    ArtifactPublished,
    /// A node joined the network.
    NodeJoined,
    /// Trust score was updated.
    TrustUpdated,
    /// Custom event type.
    Custom(String),
}

/// An immutable event representing a state change in the network.
///
/// Every event is cryptographically signed by its source, enabling
/// full auditability and trust across sovereign boundaries.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    /// Unique identifier for this event.
    pub id: ObjectId,
    /// When the event occurred.
    pub timestamp: Timestamp,
    /// The agent or node that generated this event.
    pub source: SovereignUri,
    /// The type of event.
    pub event_type: EventType,
    /// The event payload (JSON serialized).
    pub payload: String,
    /// Cryptographic signature of the event data.
    pub signature: Option<Signature>,
}

impl Event {
    /// Create a new event.
    pub fn new(source: SovereignUri, event_type: EventType, payload: impl Serialize) -> Result<Self, ss_core::error::Error> {
        let payload_str = serde_json::to_string(&payload)?;
        Ok(Self {
            id: ObjectId::new(),
            timestamp: Timestamp::now(),
            source,
            event_type,
            payload: payload_str,
            signature: None,
        })
    }

    /// Sign the event with the source's key pair.
    pub fn sign(&mut self, keypair: &KeyPair) {
        let data_to_sign = self.signing_bytes();
        self.signature = Some(Signature::sign(keypair, &data_to_sign));
    }

    /// Verify the event's signature.
    pub fn verify(&self) -> bool {
        match &self.signature {
            Some(sig) => sig.verify(&self.signing_bytes()),
            None => false, // Unsigned events are untrusted
        }
    }

    /// Helper to get consistent bytes for signing/verification.
    fn signing_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        bytes.extend_from_slice(self.id.to_string().as_bytes());
        bytes.extend_from_slice(&self.timestamp.unix_secs().to_be_bytes());
        bytes.extend_from_slice(self.source.to_string().as_bytes());
        // For simplicity in this scaffolding, we use the debug string of the enum
        bytes.extend_from_slice(format!("{:?}", self.event_type).as_bytes());
        bytes.extend_from_slice(self.payload.as_bytes());
        bytes
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ss_core::uri::UriScheme;

    #[test]
    fn event_creation_and_signing() {
        let uri = SovereignUri::new(UriScheme::Agent, "test-agent");
        let mut event = Event::new(uri, EventType::SessionCreated, serde_json::json!({"session_id": "123"})).unwrap();
        
        let kp = KeyPair::generate();
        event.sign(&kp);
        
        assert!(event.verify());
    }

    #[test]
    fn unsigned_event_fails_verification() {
        let uri = SovereignUri::new(UriScheme::Agent, "test-agent");
        let event = Event::new(uri, EventType::SessionCreated, serde_json::json!({"session_id": "123"})).unwrap();
        
        assert!(!event.verify());
    }
}
