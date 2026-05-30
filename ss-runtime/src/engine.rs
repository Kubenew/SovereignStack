//! Core abstraction for LLM inference engines.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};

/// A standardized request to any inference engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceRequest {
    /// The prompt or system instructions.
    pub prompt: String,
    /// Maximum tokens to generate.
    pub max_tokens: Option<u32>,
    /// Temperature for sampling (0.0 to 1.0).
    pub temperature: Option<f32>,
    /// Required capability context (e.g., "legal_reasoning").
    pub context: Option<String>,
}

/// A standardized response from any inference engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceResponse {
    /// The generated text.
    pub output: String,
    /// Number of tokens consumed in the prompt.
    pub prompt_tokens: u32,
    /// Number of tokens generated.
    pub completion_tokens: u32,
    /// Identifier of the model that executed this.
    pub model_id: String,
    /// Estimated cost of this execution (in abstract units).
    pub estimated_cost: f64,
}

/// The core trait that all local and cloud LLM wrappers must implement.
#[async_trait]
pub trait InferenceEngine: Send + Sync {
    /// Execute an inference request and return the result.
    async fn execute(&self, request: &InferenceRequest) -> Result<InferenceResponse, ss_core::error::Error>;
    
    /// Get the estimated latency (in ms) for a given prompt size.
    fn estimate_latency(&self, prompt_len: usize) -> u64;
    
    /// Get the estimated cost for a given prompt size.
    fn estimate_cost(&self, prompt_len: usize) -> f64;
    
    /// Check if this engine supports a specific capability context.
    fn supports_context(&self, context: &str) -> bool;
}

// Scaffolded implementations for future expansion:

/// A local inference engine (e.g., binding to llama.cpp).
pub struct LocalModelEngine {
    pub model_path: String,
    pub max_context: usize,
}

#[async_trait]
impl InferenceEngine for LocalModelEngine {
    async fn execute(&self, _request: &InferenceRequest) -> Result<InferenceResponse, ss_core::error::Error> {
        // In reality, this would FFI into llama.cpp or call a local inference server
        Ok(InferenceResponse {
            output: "Mock local execution output.".to_string(),
            prompt_tokens: 10,
            completion_tokens: 5,
            model_id: "local-llama-3-8b".to_string(),
            estimated_cost: 0.001, // Very cheap
        })
    }
    
    fn estimate_latency(&self, _prompt_len: usize) -> u64 {
        150 // Very fast latency for small prompts locally
    }
    
    fn estimate_cost(&self, _prompt_len: usize) -> f64 {
        0.001 // Basically just local electricity cost
    }
    
    fn supports_context(&self, _context: &str) -> bool {
        true // Assume the local model is a generalist
    }
}
