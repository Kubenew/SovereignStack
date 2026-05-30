//! Capability registry — the local capability index.

use std::collections::HashMap;

use crate::descriptor::CapabilityDescriptor;
use crate::query::{CapabilityMatch, CapabilityQuery};

/// A registry of advertised capabilities.
///
/// This is the core of the Agent Capability Protocol (ACP).
/// Agents register their capabilities, and other agents query
/// for capabilities they need. The registry returns ranked results.
pub struct CapabilityRegistry {
    /// All registered descriptors, keyed by capability name.
    descriptors: HashMap<String, Vec<CapabilityDescriptor>>,
}

impl CapabilityRegistry {
    /// Create a new empty registry.
    pub fn new() -> Self {
        Self {
            descriptors: HashMap::new(),
        }
    }

    /// Register a capability descriptor.
    pub fn register(&mut self, descriptor: CapabilityDescriptor) {
        self.descriptors
            .entry(descriptor.capability.clone())
            .or_default()
            .push(descriptor);
    }

    /// Query the registry for matching capabilities.
    ///
    /// Returns results sorted by relevance score (highest first).
    pub fn query(&self, query: &CapabilityQuery) -> Vec<CapabilityMatch> {
        let candidates = match self.descriptors.get(&query.capability) {
            Some(descs) => descs,
            None => return Vec::new(),
        };

        let mut matches: Vec<CapabilityMatch> = candidates
            .iter()
            .filter(|d| query.matches(d))
            .map(|d| CapabilityMatch {
                score: d.relevance_score(),
                descriptor: d.clone(),
            })
            .collect();

        // Sort by score descending
        matches.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));

        // Limit results
        matches.truncate(query.max_results);

        matches
    }

    /// Remove all capabilities for a given provider URI.
    pub fn remove_provider(&mut self, provider_uri: &str) {
        for descs in self.descriptors.values_mut() {
            descs.retain(|d| d.provider.to_string() != provider_uri);
        }
        // Remove empty entries
        self.descriptors.retain(|_, v| !v.is_empty());
    }

    /// List all known capability names.
    pub fn capability_names(&self) -> Vec<&str> {
        self.descriptors.keys().map(|k| k.as_str()).collect()
    }

    /// Returns the total number of registered descriptors.
    pub fn len(&self) -> usize {
        self.descriptors.values().map(|v| v.len()).sum()
    }

    /// Returns true if the registry is empty.
    pub fn is_empty(&self) -> bool {
        self.descriptors.is_empty()
    }

    /// Get all descriptors for a specific capability.
    pub fn get_descriptors(&self, capability: &str) -> Option<&Vec<CapabilityDescriptor>> {
        self.descriptors.get(capability)
    }
}

impl Default for CapabilityRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ss_core::uri::{SovereignUri, UriScheme};

    fn agent_uri(name: &str) -> SovereignUri {
        SovereignUri::new(UriScheme::Agent, name)
    }

    #[test]
    fn register_and_query() {
        let mut registry = CapabilityRegistry::new();

        registry.register(
            CapabilityDescriptor::new(agent_uri("agent-1"), "analysis")
                .with_accuracy(0.9)
                .with_cost(0.1)
                .with_latency_ms(500),
        );
        registry.register(
            CapabilityDescriptor::new(agent_uri("agent-2"), "analysis")
                .with_accuracy(0.7)
                .with_cost(0.05)
                .with_latency_ms(200),
        );

        let query = CapabilityQuery::new("analysis");
        let results = registry.query(&query);
        assert_eq!(results.len(), 2);

        // Higher accuracy agent should rank first
        assert!(results[0].score >= results[1].score);
    }

    #[test]
    fn query_with_filters() {
        let mut registry = CapabilityRegistry::new();

        registry.register(
            CapabilityDescriptor::new(agent_uri("expert"), "review")
                .with_accuracy(0.95)
                .with_cost(1.0),
        );
        registry.register(
            CapabilityDescriptor::new(agent_uri("novice"), "review")
                .with_accuracy(0.5)
                .with_cost(0.1),
        );

        let query = CapabilityQuery::new("review").with_min_accuracy(0.9);
        let results = registry.query(&query);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].descriptor.provider.authority(), "expert");
    }

    #[test]
    fn query_no_match() {
        let registry = CapabilityRegistry::new();
        let query = CapabilityQuery::new("nonexistent");
        let results = registry.query(&query);
        assert!(results.is_empty());
    }

    #[test]
    fn remove_provider() {
        let mut registry = CapabilityRegistry::new();

        registry.register(CapabilityDescriptor::new(agent_uri("agent-1"), "analysis"));
        registry.register(CapabilityDescriptor::new(agent_uri("agent-1"), "coding"));
        registry.register(CapabilityDescriptor::new(agent_uri("agent-2"), "analysis"));

        assert_eq!(registry.len(), 3);
        registry.remove_provider("agent://agent-1");
        assert_eq!(registry.len(), 1);
    }

    #[test]
    fn list_capabilities() {
        let mut registry = CapabilityRegistry::new();
        registry.register(CapabilityDescriptor::new(agent_uri("a"), "analysis"));
        registry.register(CapabilityDescriptor::new(agent_uri("b"), "coding"));
        registry.register(CapabilityDescriptor::new(agent_uri("c"), "review"));

        let names = registry.capability_names();
        assert_eq!(names.len(), 3);
    }
}
