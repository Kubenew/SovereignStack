//! # ss-sessiond
//!
//! The SovereignStack Session Daemon.
//!
//! This daemon is the core runtime environment for a SovereignStack node.
//! It is responsible for orchestrating the lifecycle of agent sessions,
//! managing local state (Identity and Capability registries), and
//! connecting the execution environment to the network swarm.

pub mod daemon;
pub mod session;

pub use daemon::{DaemonConfig, SessionDaemon};
pub use session::{AgentSession, SessionState};
