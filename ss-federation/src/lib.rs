//! # ss-federation
//!
//! Sovereign routing, peer discovery, and jurisdiction compliance.
//!
//! SovereignStack nodes form a federated network where each node
//! maintains sovereignty over its data while collaborating with peers.
//!
//! ## Core Features
//!
//! - **Peer Discovery** — Finding other sovereign nodes
//! - **Sovereign Routing** — Routing tasks based on capability and trust
//! - **Jurisdiction Compliance** — Enforcing data residency rules

pub mod node;
pub mod policy;
pub mod network;
pub mod rpc;

pub use node::{NetworkNode, PeerState};
