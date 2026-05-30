//! # ss-capability
//!
//! DNS for intelligence — capability-based discovery and matching
//! in the Sovereign Intelligence Network.
//!
//! Instead of asking a specific agent to perform a task, agents ask
//! the network for a capability, and the best match wins.
//!
//! ## Example
//!
//! ```rust,no_run
//! use ss_capability::{CapabilityQuery, CapabilityRegistry, CapabilityDescriptor};
//! use ss_core::uri::{SovereignUri, UriScheme};
//!
//! let mut registry = CapabilityRegistry::new();
//!
//! // Agent advertises capabilities
//! let descriptor = CapabilityDescriptor::new(
//!     SovereignUri::new(UriScheme::Agent, "legal-agent"),
//!     "contract_review",
//! )
//! .with_accuracy(0.94)
//! .with_cost(0.02)
//! .with_latency_ms(3000);
//!
//! registry.register(descriptor);
//!
//! // Another agent queries for capability
//! let query = CapabilityQuery::new("contract_review");
//! let results = registry.query(&query);
//! ```

pub mod descriptor;
pub mod query;
pub mod registry;

pub use descriptor::CapabilityDescriptor;
pub use query::CapabilityQuery;
pub use registry::CapabilityRegistry;
