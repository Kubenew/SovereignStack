//! # ss-cas
//!
//! Content-Addressed Storage (CAS) for SovereignStack.
//!
//! Implements Merkle Memory Trees (Future-Proof Addition #5).
//! Instead of relying on traditional databases where locations are mutable,
//! all knowledge, memory, and artifacts are addressed by their cryptographic hash.
//!
//! ## Core Properties
//!
//! - **Immutability** — Data cannot change once written.
//! - **Reproducibility** — The same inputs always yield the same hash.
//! - **Auditability** — Merkle structures allow verifiable proofs.
//! - **Synchronization** — Efficient sync by comparing tree roots.

pub mod store;
pub mod node;

pub use store::CasStore;
pub use node::{MerkleNode, MerkleTree};
