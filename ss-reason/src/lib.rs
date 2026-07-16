//! # ss-reason
//!
//! SovereignStack Reasoning Objects and Caching.
//!
//! Implements verifiable reasoning graph nodes and semantic caching
//! as part of the Cognitive Mesh Architecture (RFC-0060).

use ss_core::uri::SovereignUri;
use std::collections::HashMap;

pub struct ReasoningNode {
    pub uri: SovereignUri, // reason://sha256:...
    pub content: String,
    pub parent_nodes: Vec<SovereignUri>,
    pub signature: String,
}

pub struct ReasoningGraph {
    nodes: HashMap<SovereignUri, ReasoningNode>,
}

impl ReasoningGraph {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
        }
    }

    pub fn add_node(&mut self, node: ReasoningNode) {
        self.nodes.insert(node.uri.clone(), node);
    }

    pub fn get_node(&self, uri: &SovereignUri) -> Option<&ReasoningNode> {
        self.nodes.get(uri)
    }
}

#[async_trait::async_trait]
pub trait CognitiveCache: Send + Sync {
    async fn get_cached_reasoning(&self, semantic_hash: &str) -> Option<ReasoningNode>;
    async fn cache_reasoning(&self, semantic_hash: &str, node: ReasoningNode) -> Result<(), String>;
}
