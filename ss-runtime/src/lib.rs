//! # ss-runtime
//!
//! Multi-Model Execution Runtime for SovereignStack.
//!
//! SovereignStack itself does not embed a single LLM. Instead, it defines
//! the `ss-runtime` abstraction layer which routes inference requests to the
//! optimal model—whether that is a local edge model (e.g., via `llama.cpp`),
//! a homelab GPU cluster, or a cloud provider API.
//!
//! ## Core Traits
//!
//! - `InferenceEngine` — The trait implemented by specific model wrappers.
//! - `ModelRouter` — The component that selects the best engine based on
//!   cost, latency, and capability requirements.

pub mod engine;
pub mod router;

pub use engine::{InferenceEngine, InferenceRequest, InferenceResponse};
pub use router::ModelRouter;
