//! # ss-eventbus
//!
//! Event sourcing infrastructure for SovereignStack.
//!
//! Event sourcing replaces traditional CRUD databases as the primary
//! state management pattern in SovereignStack. Every state change is
//! an immutable, cryptographically signed event.
//!
//! ## Core Concepts
//!
//! - **Event** — An immutable record of a state change
//! - **Event Stream** — An append-only log of events
//! - **Subscription** — Listening for specific events
//!
//! ## Event Types
//!
//! ```text
//! SessionCreated
//! TaskStarted
//! ArtifactPublished
//! NodeJoined
//! TrustChanged
//! ```

pub mod event;
pub mod stream;

pub use event::{Event, EventType};
pub use stream::{EventStream, EventSubscription};
