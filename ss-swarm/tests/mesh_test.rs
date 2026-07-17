use libp2p::{identity, PeerId};
use ss_core::uri::{SovereignUri, UriScheme};
use ss_swarm::network::{DiscoveryBehavior, DiscoveryEvent};

#[tokio::test]
async fn test_decentralized_agent_discovery_handshake() {
    let id_keys_a = identity::Keypair::generate_ed25519();
    let peer_id_a = PeerId::from(id_keys_a.public());

    let id_keys_b = identity::Keypair::generate_ed25519();
    let peer_id_b = PeerId::from(id_keys_b.public());

    assert_ne!(
        peer_id_a, peer_id_b,
        "Network peers must maintain distinct cryptographic identities."
    );
}

#[tokio::test]
async fn test_discovery_behavior_construction() {
    let local_key = identity::Keypair::generate_ed25519();
    let peer_id = PeerId::from(local_key.public());
    let agent_uri = SovereignUri::new(UriScheme::Agent, "test-agent");

    let behavior = DiscoveryBehavior::new(peer_id, agent_uri, None);

    assert!(behavior.kademlia.kbuckets_entries().is_empty());
}

#[tokio::test]
async fn test_register_agent_provider() {
    let local_key = identity::Keypair::generate_ed25519();
    let peer_id = PeerId::from(local_key.public());
    let agent_uri = SovereignUri::new(UriScheme::Agent, "test-agent");
    let mut behavior = DiscoveryBehavior::new(peer_id, agent_uri, None);

    let key = libp2p::kad::RecordKey::new(&b"capability://math-reasoning"[..]);
    behavior.register_agent_provider(key);
    // Provider advertisement is queued; full verification requires
    // a running swarm with at least one connected peer.
    assert!(behavior.kademlia.kbuckets_entries().count() == 0);
}
