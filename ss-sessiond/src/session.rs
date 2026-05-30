//! Agent session representation.

use serde::{Deserialize, Serialize};
use ss_core::timestamp::Timestamp;
use ss_core::uri::SovereignUri;
use ss_identity::AgentIdentity;
use tracing::info;

/// The execution state of an agent session.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SessionState {
    /// Being set up.
    Initializing,
    /// Actively executing / listening.
    Running,
    /// Paused (e.g., waiting for resources or events).
    Suspended,
    /// Successfully shut down.
    Terminated,
    /// Shut down due to an error.
    Failed,
}

/// An active execution session for an agent.
///
/// Implements the process-isolation level of the architecture. Each session
/// binds to a Universal Agent Identity and provides the runtime environment
/// (Memory, Capabilities, Messaging) for that specific agent.
pub struct AgentSession {
    /// The identity bound to this session.
    identity: AgentIdentity,
    /// Current execution state.
    state: SessionState,
    /// When the session was started.
    started_at: Option<Timestamp>,
}

impl AgentSession {
    /// Create a new session for an identity.
    pub fn new(identity: AgentIdentity) -> Self {
        Self {
            identity,
            state: SessionState::Initializing,
            started_at: None,
        }
    }

    /// Start the session execution.
    pub async fn start(&mut self) -> Result<(), ss_core::error::Error> {
        self.state = SessionState::Running;
        self.started_at = Some(Timestamp::now());
        info!("Session started for agent: {}", self.identity.uri());
        
        // Setup isolation: in v2, this would spawn a Wasm runtime or container
        
        Ok(())
    }

    /// Suspend the session.
    pub async fn suspend(&mut self) -> Result<(), ss_core::error::Error> {
        self.state = SessionState::Suspended;
        info!("Session suspended for agent: {}", self.identity.uri());
        Ok(())
    }

    /// Terminate the session cleanly.
    pub async fn terminate(&mut self) -> Result<(), ss_core::error::Error> {
        self.state = SessionState::Terminated;
        info!("Session terminated for agent: {}", self.identity.uri());
        Ok(())
    }

    /// Get the session state.
    pub fn state(&self) -> SessionState {
        self.state
    }

    /// Get the associated identity URI.
    pub fn uri(&self) -> &SovereignUri {
        self.identity.uri()
    }
}
