//! Network transport layer based on libp2p.

use libp2p::{
    gossipsub, kad, mdns, request_response, swarm::NetworkBehaviour,
};

/// The unified network behaviour for SovereignStack.
///
/// Combines:
/// - Kademlia DHT for session and capability discovery
/// - Gossipsub for the Sovereign Event Bus
/// - Request-Response for direct RPC (e.g., capability queries)
/// - mDNS for local peer discovery
#[derive(NetworkBehaviour)]
pub struct SovereignBehaviour {
    pub kademlia: kad::Behaviour<kad::store::MemoryStore>,
    pub gossipsub: gossipsub::Behaviour,
    pub mdns: mdns::tokio::Behaviour,
    // Note: Request/Response behaviour would be added here
    // based on our protobuf definitions in `rpc.rs`
}

impl SovereignBehaviour {
    /// Create a new SovereignBehaviour.
    pub fn new(local_peer_id: libp2p::PeerId) -> Self {
        // Initialize Kademlia
        let store = kad::store::MemoryStore::new(local_peer_id);
        let kademlia = kad::Behaviour::new(local_peer_id, store);

        // Initialize Gossipsub
        let gossipsub_config = gossipsub::ConfigBuilder::default()
            .max_transmit_size(1024 * 1024) // 1MB max event size
            .build()
            .expect("Valid gossipsub config");
        
        let message_authenticity = gossipsub::MessageAuthenticity::Anonymous; // Authentication is handled at the SovereignStack protocol layer
        let gossipsub = gossipsub::Behaviour::new(message_authenticity, gossipsub_config)
            .expect("Valid gossipsub behaviour");

        // Initialize mDNS
        let mdns = mdns::tokio::Behaviour::new(mdns::Config::default(), local_peer_id)
            .expect("Valid mDNS config");

        Self {
            kademlia,
            gossipsub,
            mdns,
        }
    }
}
