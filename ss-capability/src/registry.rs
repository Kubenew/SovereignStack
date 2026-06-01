//! Capability registry — the local capability index with bindings and revocation.

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use ss_core::timestamp::Timestamp;
use ss_core::uri::SovereignUri;

use crate::descriptor::CapabilityDescriptor;
use crate::query::{CapabilityMatch, CapabilityQuery};

/// A binding represents an active use of a capability by a consumer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityBinding {
    pub id: String,
    pub capability: String,
    pub consumer: SovereignUri,
    pub provider: SovereignUri,
    pub status: BindingStatus,
    pub created: Timestamp,
    pub expires: Option<Timestamp>,
    pub max_calls: Option<u64>,
    pub calls_made: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BindingStatus {
    Active,
    Suspended,
    Revoked,
    Expired,
}

/// A registry of advertised capabilities with binding and revocation support.
pub struct CapabilityRegistry {
    descriptors: HashMap<String, Vec<CapabilityDescriptor>>,
    bindings: HashMap<String, CapabilityBinding>,
    revoked: Vec<String>,
    revoked_providers: Vec<String>,
}

impl CapabilityRegistry {
    pub fn new() -> Self {
        Self {
            descriptors: HashMap::new(),
            bindings: HashMap::new(),
            revoked: Vec::new(),
            revoked_providers: Vec::new(),
        }
    }

    /// Register a capability descriptor.
    pub fn register(&mut self, descriptor: CapabilityDescriptor) {
        if self.revoked_providers.contains(&descriptor.provider.to_string()) {
            return;
        }
        self.descriptors
            .entry(descriptor.capability.clone())
            .or_default()
            .push(descriptor);
    }

    /// Query the registry for matching capabilities.
    pub fn query(&self, query: &CapabilityQuery) -> Vec<CapabilityMatch> {
        let candidates = match self.descriptors.get(&query.capability) {
            Some(descs) => descs,
            None => return Vec::new(),
        };

        let mut matches: Vec<CapabilityMatch> = candidates
            .iter()
            .filter(|d| {
                query.matches(d)
                    && d.available
                    && !self.revoked_providers.contains(&d.provider.to_string())
                    && d.expires_at.map(|e| e > Timestamp::now()).unwrap_or(true)
            })
            .map(|d| CapabilityMatch {
                score: d.relevance_score(),
                descriptor: d.clone(),
            })
            .collect();

        matches.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        matches.truncate(query.max_results);
        matches
    }

    /// Bind a consumer to a capability (reserve usage).
    pub fn create_binding(
        &mut self,
        capability: &str,
        consumer: SovereignUri,
        provider: SovereignUri,
        max_calls: Option<u64>,
        ttl_secs: Option<u64>,
    ) -> Option<CapabilityBinding> {
        let binding = CapabilityBinding {
            id: format!("binding://{}/{}", capability, uuid::Uuid::new_v4()),
            capability: capability.to_string(),
            consumer,
            provider,
            status: BindingStatus::Active,
            created: Timestamp::now(),
            expires: ttl_secs.map(|s| {
                let now = Timestamp::now();
                Timestamp::from_utc(
                    *now.as_datetime() + chrono::Duration::seconds(s as i64)
                )
            }),
            max_calls,
            calls_made: 0,
        };
        let id = binding.id.clone();
        self.bindings.insert(id, binding.clone());
        Some(binding)
    }

    /// Record a call against a binding.
    pub fn use_binding(&mut self, binding_id: &str) -> bool {
        if let Some(binding) = self.bindings.get_mut(binding_id) {
            if binding.status != BindingStatus::Active {
                return false;
            }
            if let Some(expires) = binding.expires {
                if Timestamp::now() > expires {
                    binding.status = BindingStatus::Expired;
                    return false;
                }
            }
            if let Some(max) = binding.max_calls {
                if binding.calls_made >= max {
                    binding.status = BindingStatus::Expired;
                    return false;
                }
            }
            binding.calls_made += 1;
            true
        } else {
            false
        }
    }

    /// Revoke a specific capability binding.
    pub fn revoke_binding(&mut self, binding_id: &str) {
        if let Some(binding) = self.bindings.get_mut(binding_id) {
            binding.status = BindingStatus::Revoked;
        }
    }

    /// Revoke all capabilities for a provider.
    pub fn revoke_provider(&mut self, provider_uri: &str) {
        self.revoked_providers.push(provider_uri.to_string());
        for descs in self.descriptors.values_mut() {
            descs.retain(|d| d.provider.to_string() != provider_uri);
        }
        self.descriptors.retain(|_, v| !v.is_empty());
        for binding in self.bindings.values_mut() {
            if binding.provider.to_string() == provider_uri {
                binding.status = BindingStatus::Revoked;
            }
        }
    }

    /// Remove all capabilities for a given provider URI (soft removal).
    pub fn remove_provider(&mut self, provider_uri: &str) {
        for descs in self.descriptors.values_mut() {
            descs.retain(|d| d.provider.to_string() != provider_uri);
        }
        self.descriptors.retain(|_, v| !v.is_empty());
    }

    /// List all active bindings.
    pub fn active_bindings(&self) -> Vec<&CapabilityBinding> {
        self.bindings.values().filter(|b| b.status == BindingStatus::Active).collect()
    }

    /// List all known capability names.
    pub fn capability_names(&self) -> Vec<&str> {
        self.descriptors.keys().map(|k| k.as_str()).collect()
    }

    pub fn len(&self) -> usize {
        self.descriptors.values().map(|v| v.len()).sum()
    }

    pub fn is_empty(&self) -> bool {
        self.descriptors.is_empty()
    }

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
                .with_accuracy(0.9).with_cost(0.1).with_latency_ms(500),
        );
        registry.register(
            CapabilityDescriptor::new(agent_uri("agent-2"), "analysis")
                .with_accuracy(0.7).with_cost(0.05).with_latency_ms(200),
        );
        let query = CapabilityQuery::new("analysis");
        let results = registry.query(&query);
        assert_eq!(results.len(), 2);
        assert!(results[0].score >= results[1].score);
    }

    #[test]
    fn query_with_filters() {
        let mut registry = CapabilityRegistry::new();
        registry.register(
            CapabilityDescriptor::new(agent_uri("expert"), "review")
                .with_accuracy(0.95).with_cost(1.0),
        );
        registry.register(
            CapabilityDescriptor::new(agent_uri("novice"), "review")
                .with_accuracy(0.5).with_cost(0.1),
        );
        let query = CapabilityQuery::new("review").with_min_accuracy(0.9);
        let results = registry.query(&query);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].descriptor.provider.authority(), "expert");
    }

    #[test]
    fn create_and_use_binding() {
        let mut registry = CapabilityRegistry::new();
        let consumer = agent_uri("consumer");
        let provider = agent_uri("provider");
        let binding = registry.create_binding("analysis", consumer, provider, Some(5), Some(3600));
        assert!(binding.is_some());
        assert!(registry.use_binding(&binding.unwrap().id));
    }

    #[test]
    fn binding_max_calls() {
        let mut registry = CapabilityRegistry::new();
        let binding = registry.create_binding("test", agent_uri("c"), agent_uri("p"), Some(2), None).unwrap();
        assert!(registry.use_binding(&binding.id));
        assert!(registry.use_binding(&binding.id));
        assert!(!registry.use_binding(&binding.id));
    }

    #[test]
    fn revoke_provider_removes_descriptors() {
        let mut registry = CapabilityRegistry::new();
        registry.register(CapabilityDescriptor::new(agent_uri("bad"), "analysis"));
        assert_eq!(registry.len(), 1);
        registry.revoke_provider("agent://bad");
        assert_eq!(registry.len(), 0);
    }

    #[test]
    fn query_after_expiry() {
        let mut registry = CapabilityRegistry::new();
        let past = Timestamp::now();
        let desc = CapabilityDescriptor {
            provider: agent_uri("expired"),
            capability: "stale".into(),
            description: None,
            accuracy: 0.9,
            cost: 0.1,
            latency_ms: 100,
            max_concurrency: 1,
            languages: vec![],
            jurisdictions: vec![],
            tags: vec![],
            published_at: past,
            expires_at: Some(past),
            available: true,
            version: "1.0".into(),
        };
        registry.register(desc);
        let query = CapabilityQuery::new("stale");
        assert!(registry.query(&query).is_empty());
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
