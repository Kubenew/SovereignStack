use std::collections::HashSet;
use std::time::Duration;

use libp2p::{
    identify, kad, mdns, request_response, swarm::NetworkBehaviour, StreamProtocol,
};

use ss_core::uri::{SovereignUri, UriScheme};

pub type PeerId = libp2p::PeerId;

/// Capability record an agent advertises on the DHT.
#[derive(Debug, Clone)]
pub struct AgentCapability {
    pub agent_uri: SovereignUri,
    pub supported_capabilities: Vec<String>,
    pub kv_cache_load: f64,
}

/// Events emitted by DiscoveryBehavior.
#[derive(Debug)]
pub enum DiscoveryEvent {
    PeerDiscovered(PeerId, Vec<AgentCapability>),
    PeerLost(PeerId),
    CapabilityQueryResult(PeerId, Option<AgentCapability>),
}

#[derive(NetworkBehaviour)]
pub struct DiscoveryBehavior {
    /// Kademlia DHT for decentralized peer discovery and provider records.
    pub kademlia: kad::Behaviour<kad::store::MemoryStore>,

    /// mDNS for zero-config local-network peer discovery.
    pub mdns: mdns::tokio::Behaviour,

    /// Identify protocol for exchanging peer metadata.
    pub identify: identify::Behaviour,

    /// Direct request/response for agent capability queries.
    pub capability_exchange: request_response::Behaviour<CapabilityRequest, CapabilityResponse>,
}

impl DiscoveryBehavior {
    pub fn new(
        local_peer_id: PeerId,
        local_agent_uri: SovereignUri,
        bootstrap_peers: Option<Vec<std::net::Multiaddr>>,
    ) -> Self {
        let store = kad::store::MemoryStore::new(local_peer_id);
        let kademlia = kad::Behaviour::new(
            local_peer_id,
            store,
        );

        let mdns = mdns::tokio::Behaviour::new(
            mdns::Config::default(),
            local_peer_id,
        )
        .expect("mDNS initialized");

        let identify = identify::Behaviour::new(
            identify::Config::new(
                format!("sovereignstack/{}", local_agent_uri),
                local_peer_id,
            )
            .with_interval(Duration::from_secs(60)),
        );

        let capability_exchange =
            request_response::Behaviour::new(
                [(
                    StreamProtocol::new("/sovereignstack/capability/1"),
                    request_response::ProtocolSupport::Full,
                )],
                request_response::Config::default(),
            );

        Self {
            kademlia,
            mdns,
            identify,
            capability_exchange,
        }
    }

    pub fn register_agent_provider(
        &mut self,
        key: kad::RecordKey,
    ) {
        self.kademlia.start_providing(key).ok();
    }
}

#[derive(Debug, Clone)]
pub struct CapabilityRequest(pub Vec<u8>);

impl request_response::Codec for CapabilityRequest {
    type Proto = Vec<u8>;
    fn read_bytes(&mut self, bytes: &[u8]) -> Result<Vec<u8>, std::io::Error> {
        Ok(bytes.to_vec())
    }
    fn write_bytes(&mut self, data: &[u8]) -> Result<Vec<u8>, std::io::Error> {
        Ok(data.to_vec())
    }
}

#[derive(Debug, Clone)]
pub struct CapabilityResponse(pub Vec<u8>);

impl request_response::Codec for CapabilityResponse {
    type Proto = Vec<u8>;
    fn read_bytes(&mut self, bytes: &[u8]) -> Result<Vec<u8>, std::io::Error> {
        Ok(bytes.to_vec())
    }
    fn write_bytes(&mut self, data: &[u8]) -> Result<Vec<u8>, std::io::Error> {
        Ok(data.to_vec())
    }
}
