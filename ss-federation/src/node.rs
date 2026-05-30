//! Network node representation and peer state.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

use ss_core::timestamp::Timestamp;
use ss_core::uri::SovereignUri;
use ss_identity::AgentIdentity;

/// State of a known peer in the federation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerState {
    pub uri: SovereignUri,
    pub address: String, // E.g., IP or domain
    pub last_seen: Timestamp,
    pub latency_ms: u64,
    pub is_online: bool,
    pub trust_score: f64,
}

/// A node in the Sovereign Intelligence Network.
pub struct NetworkNode {
    pub identity: AgentIdentity,
    peers: Arc<RwLock<HashMap<String, PeerState>>>,
}

impl NetworkNode {
    /// Create a new network node.
    pub fn new(identity: AgentIdentity) -> Self {
        Self {
            identity,
            peers: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Add a peer to the node's routing table.
    pub async fn add_peer(&self, peer: PeerState) {
        let mut peers = self.peers.write().await;
        peers.insert(peer.uri.to_string(), peer);
    }

    /// Get a peer's state.
    pub async fn get_peer(&self, uri: &SovereignUri) -> Option<PeerState> {
        let peers = self.peers.read().await;
        peers.get(&uri.to_string()).cloned()
    }
    
    /// Get all known peers.
    pub async fn peers(&self) -> Vec<PeerState> {
        let peers = self.peers.read().await;
        peers.values().cloned().collect()
    }
}
