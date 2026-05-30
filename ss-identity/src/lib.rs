//! # ss-identity
//!
//! Universal Agent Identity (UAI) for the SovereignStack network.
//!
//! Every participant in the Sovereign Intelligence Network — agents,
//! organizations, robots, services — gets a persistent, cryptographically
//! verifiable identity.
//!
//! ## Identity Components
//!
//! Each identity has:
//! - **URI** — globally addressable identity (`agent://researcher-1`)
//! - **Public Key** — Ed25519 for signing and verification
//! - **Capabilities** — what this identity can do
//! - **Trust Score** — earned reputation
//! - **Jurisdiction** — sovereign compliance metadata
//!
//! ## Identity Types
//!
//! ```text
//! agent://   — AI agents
//! org://     — Organizations
//! robot://   — Physical devices
//! node://    — Network nodes
//! ```
//!
//! ## Example
//!
//! ```rust,no_run
//! use ss_identity::{AgentIdentity, IdentityType};
//!
//! let identity = AgentIdentity::create("researcher-1", IdentityType::Agent);
//! println!("URI: {}", identity.uri());
//! println!("Public Key: {}", identity.public_key());
//! ```

pub mod identity;
pub mod registry;
pub mod trust;

pub use identity::{AgentIdentity, IdentityType};
pub use registry::IdentityRegistry;
pub use trust::TrustProfile;
