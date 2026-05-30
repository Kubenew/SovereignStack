//! # ss-core
//!
//! Core types, URI parsing, and shared primitives for the SovereignStack
//! Sovereign Intelligence Network.
//!
//! This crate provides the foundational abstractions that all SovereignStack
//! subsystems depend on:
//!
//! - [`SovereignUri`] — Universal addressing for all network objects
//! - [`Timestamp`] — Temporal types with validity windows
//! - [`Error`] / [`Result`] — Unified error handling
//!
//! ## Universal Addressing
//!
//! Every object in SovereignStack is addressable via a [`SovereignUri`]:
//!
//! ```rust
//! use ss_core::SovereignUri;
//!
//! let agent = SovereignUri::parse("agent://researcher-1").unwrap();
//! let knowledge = SovereignUri::parse("knowledge://physics/newton").unwrap();
//! let capability = SovereignUri::parse("capability://legal-review").unwrap();
//! ```

pub mod uri;
pub mod timestamp;
pub mod error;
pub mod types;

pub use uri::{SovereignUri, UriScheme};
pub use timestamp::Timestamp;
pub use error::{Error, Result};
pub use types::*;
