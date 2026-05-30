//! The core daemon managing the node runtime.

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn};

use ss_capability::CapabilityRegistry;
use ss_core::uri::SovereignUri;
use ss_eventbus::EventStream;
use ss_identity::{AgentIdentity, IdentityRegistry};

use crate::session::AgentSession;

/// Configuration for the Session Daemon.
#[derive(Debug, Clone)]
pub struct DaemonConfig {
    pub bind_address: String,
    pub max_sessions: usize,
}

impl Default for DaemonConfig {
    fn default() -> Self {
        Self {
            bind_address: "127.0.0.1:9090".to_string(),
            max_sessions: 100,
        }
    }
}

/// The Session Daemon process orchestrator.
///
/// Holds the local registries (Identity, Capability), the event bus,
/// and manages active agent sessions running on this node.
pub struct SessionDaemon {
    config: DaemonConfig,
    /// The node's own cryptographic identity.
    node_identity: AgentIdentity,
    /// Local registry of known identities.
    identity_registry: Arc<RwLock<IdentityRegistry>>,
    /// Local registry of advertised capabilities.
    capability_registry: Arc<RwLock<CapabilityRegistry>>,
    /// The event bus for this node.
    event_bus: Arc<EventStream>,
    /// Active agent sessions managed by this daemon.
    sessions: Arc<RwLock<HashMap<SovereignUri, AgentSession>>>,
}

impl SessionDaemon {
    /// Initialize a new SessionDaemon.
    pub fn new(node_identity: AgentIdentity, config: DaemonConfig) -> Self {
        info!("Initializing SovereignStack Session Daemon...");
        info!("Node Identity: {}", node_identity.uri());

        let mut identity_registry = IdentityRegistry::new();
        // Register the node's own identity
        identity_registry.register_local(AgentIdentity::from_public_key(
            node_identity.name(),
            node_identity.identity_type(),
            node_identity.public_key().clone(),
        ));

        Self {
            config,
            node_identity,
            identity_registry: Arc::new(RwLock::new(identity_registry)),
            capability_registry: Arc::new(RwLock::new(CapabilityRegistry::new())),
            event_bus: Arc::new(EventStream::new()),
            sessions: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Start the daemon loops.
    pub async fn start(&self) -> Result<(), ss_core::error::Error> {
        info!("Starting Session Daemon on {}", self.config.bind_address);

        // In a full implementation, we would spawn:
        // 1. TCP Server for local CLI requests
        // 2. Event bus subscriber loop
        // 3. Libp2p network swarm bridge
        // 4. Session resource monitor

        // We block here conceptually
        Ok(())
    }

    /// Spawn a new agent session.
    pub async fn spawn_session(&self, agent_identity: AgentIdentity) -> Result<SovereignUri, ss_core::error::Error> {
        let uri = agent_identity.uri().clone();
        
        let mut sessions = self.sessions.write().await;
        if sessions.len() >= self.config.max_sessions {
            warn!("Max sessions reached ({})", self.config.max_sessions);
            return Err(ss_core::error::Error::Internal("Max sessions reached".to_string()));
        }

        if sessions.contains_key(&uri) {
            return Err(ss_core::error::Error::Internal("Session already active".to_string()));
        }

        let mut session = AgentSession::new(agent_identity);
        session.start().await?;
        
        sessions.insert(uri.clone(), session);
        info!("Spawned new session for {}", uri);

        Ok(uri)
    }

    /// Terminate an active session.
    pub async fn terminate_session(&self, uri: &SovereignUri) -> Result<(), ss_core::error::Error> {
        let mut sessions = self.sessions.write().await;
        if let Some(mut session) = sessions.remove(uri) {
            session.terminate().await?;
            info!("Terminated session for {}", uri);
            Ok(())
        } else {
            Err(ss_core::error::Error::Internal("Session not found".to_string()))
        }
    }

    /// Get a count of active sessions.
    pub async fn active_sessions_count(&self) -> usize {
        self.sessions.read().await.len()
    }
}
