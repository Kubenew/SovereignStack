//! Model Router for dynamic inference engine selection.

use tracing::info;
use crate::engine::{InferenceEngine, InferenceRequest, InferenceResponse};
use std::sync::Arc;

/// Strategy for routing a request to an engine.
pub enum RoutingStrategy {
    LowestCost,
    LowestLatency,
    RequireContext(String),
}

/// The Model Router decides which inference engine executes a given request.
///
/// Implements Future-Proof Addition #11 (Multi-Model Runtime) and #9 (Compute Scheduling).
pub struct ModelRouter {
    engines: Vec<Arc<dyn InferenceEngine>>,
}

impl ModelRouter {
    pub fn new() -> Self {
        Self {
            engines: Vec::new(),
        }
    }

    /// Register an inference engine with the router.
    pub fn register_engine(&mut self, engine: Arc<dyn InferenceEngine>) {
        self.engines.push(engine);
    }

    /// Route a request to the best engine and execute it.
    pub async fn route_and_execute(
        &self,
        request: &InferenceRequest,
        strategy: RoutingStrategy,
    ) -> Result<InferenceResponse, ss_core::error::Error> {
        if self.engines.is_empty() {
            return Err(ss_core::error::Error::Internal("No inference engines registered".to_string()));
        }

        let prompt_len = request.prompt.len();
        
        // Find the best engine based on strategy
        let best_engine = match strategy {
            RoutingStrategy::LowestCost => {
                self.engines.iter().min_by(|a, b| {
                    a.estimate_cost(prompt_len).total_cmp(&b.estimate_cost(prompt_len))
                })
            },
            RoutingStrategy::LowestLatency => {
                self.engines.iter().min_by_key(|e| e.estimate_latency(prompt_len))
            },
            RoutingStrategy::RequireContext(ctx) => {
                self.engines.iter().find(|e| e.supports_context(&ctx))
            }
        }.ok_or_else(|| ss_core::error::Error::Internal("No suitable engine found for strategy".to_string()))?;

        info!("Routing request to engine (estimated cost: {})", best_engine.estimate_cost(prompt_len));
        best_engine.execute(request).await
    }
}

impl Default for ModelRouter {
    fn default() -> Self {
        Self::new()
    }
}
