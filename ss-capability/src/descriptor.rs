//! Capability descriptors — what agents can do.

use serde::{Deserialize, Serialize};
use ss_core::timestamp::Timestamp;
use ss_core::uri::SovereignUri;

/// Describes a capability that an agent offers to the network.
///
/// This is the "advertisement" that agents publish so others can
/// discover them through capability-based routing (Semantic DNS).
///
/// Analogous to a DNS record + package metadata combined.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityDescriptor {
    /// The agent providing this capability.
    pub provider: SovereignUri,
    /// The capability name (e.g., "contract_review", "code_generation").
    pub capability: String,
    /// Human-readable description.
    pub description: Option<String>,
    /// Historical accuracy (0.0 to 1.0).
    pub accuracy: f64,
    /// Cost per invocation (abstract units).
    pub cost: f64,
    /// Expected latency in milliseconds.
    pub latency_ms: u64,
    /// Maximum concurrent requests.
    pub max_concurrency: u32,
    /// Supported languages (e.g., ["en", "cs", "de"]).
    pub languages: Vec<String>,
    /// Required jurisdictions (e.g., ["EU", "US"]).
    pub jurisdictions: Vec<String>,
    /// Tags for additional filtering.
    pub tags: Vec<String>,
    /// When this descriptor was published.
    pub published_at: Timestamp,
    /// When this descriptor expires (None = never).
    pub expires_at: Option<Timestamp>,
    /// Whether this capability is currently available.
    pub available: bool,
    /// Version of the capability implementation.
    pub version: String,
}

impl CapabilityDescriptor {
    /// Create a new capability descriptor.
    pub fn new(provider: SovereignUri, capability: &str) -> Self {
        Self {
            provider,
            capability: capability.to_string(),
            description: None,
            accuracy: 0.0,
            cost: 0.0,
            latency_ms: 0,
            max_concurrency: 1,
            languages: Vec::new(),
            jurisdictions: Vec::new(),
            tags: Vec::new(),
            published_at: Timestamp::now(),
            expires_at: None,
            available: true,
            version: "0.1.0".to_string(),
        }
    }

    /// Set the accuracy score.
    pub fn with_accuracy(mut self, accuracy: f64) -> Self {
        self.accuracy = accuracy.clamp(0.0, 1.0);
        self
    }

    /// Set the cost per invocation.
    pub fn with_cost(mut self, cost: f64) -> Self {
        self.cost = cost;
        self
    }

    /// Set the expected latency.
    pub fn with_latency_ms(mut self, latency_ms: u64) -> Self {
        self.latency_ms = latency_ms;
        self
    }

    /// Set the maximum concurrency.
    pub fn with_max_concurrency(mut self, max: u32) -> Self {
        self.max_concurrency = max;
        self
    }

    /// Set supported languages.
    pub fn with_languages(mut self, languages: Vec<String>) -> Self {
        self.languages = languages;
        self
    }

    /// Set jurisdictions.
    pub fn with_jurisdictions(mut self, jurisdictions: Vec<String>) -> Self {
        self.jurisdictions = jurisdictions;
        self
    }

    /// Set description.
    pub fn with_description(mut self, desc: &str) -> Self {
        self.description = Some(desc.to_string());
        self
    }

    /// Set tags.
    pub fn with_tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }

    /// Set version.
    pub fn with_version(mut self, version: &str) -> Self {
        self.version = version.to_string();
        self
    }

    /// Compute a relevance score against a query.
    ///
    /// Higher scores indicate better matches. Factors in accuracy,
    /// cost, and latency to find the best provider for a request.
    pub fn relevance_score(&self) -> f64 {
        // Weighted: accuracy most important, then latency, then cost
        let latency_score = 1.0 - (self.latency_ms as f64 / 30000.0).min(1.0);
        let cost_score = 1.0 - (self.cost / 10.0).min(1.0);

        self.accuracy * 0.5 + latency_score * 0.3 + cost_score * 0.2
    }

    /// Check if this capability matches a given language.
    pub fn supports_language(&self, lang: &str) -> bool {
        self.languages.is_empty() || self.languages.iter().any(|l| l == lang)
    }

    /// Check if this capability is valid in a jurisdiction.
    pub fn supports_jurisdiction(&self, jurisdiction: &str) -> bool {
        self.jurisdictions.is_empty()
            || self.jurisdictions.iter().any(|j| j == jurisdiction)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ss_core::uri::UriScheme;

    #[test]
    fn create_descriptor() {
        let uri = SovereignUri::new(UriScheme::Agent, "legal-agent");
        let desc = CapabilityDescriptor::new(uri, "contract_review")
            .with_accuracy(0.94)
            .with_cost(0.02)
            .with_latency_ms(3000);

        assert_eq!(desc.capability, "contract_review");
        assert_eq!(desc.accuracy, 0.94);
        assert_eq!(desc.cost, 0.02);
        assert_eq!(desc.latency_ms, 3000);
        assert!(desc.available);
    }

    #[test]
    fn relevance_scoring() {
        let uri = SovereignUri::new(UriScheme::Agent, "agent-1");
        let high_quality = CapabilityDescriptor::new(uri.clone(), "test")
            .with_accuracy(0.95)
            .with_latency_ms(100)
            .with_cost(0.01);

        let low_quality = CapabilityDescriptor::new(uri, "test")
            .with_accuracy(0.50)
            .with_latency_ms(10000)
            .with_cost(5.0);

        assert!(high_quality.relevance_score() > low_quality.relevance_score());
    }

    #[test]
    fn language_support() {
        let uri = SovereignUri::new(UriScheme::Agent, "agent");
        let desc = CapabilityDescriptor::new(uri, "review")
            .with_languages(vec!["en".to_string(), "cs".to_string()]);

        assert!(desc.supports_language("en"));
        assert!(desc.supports_language("cs"));
        assert!(!desc.supports_language("de"));
    }

    #[test]
    fn empty_languages_matches_all() {
        let uri = SovereignUri::new(UriScheme::Agent, "agent");
        let desc = CapabilityDescriptor::new(uri, "review");
        assert!(desc.supports_language("any"));
    }

    #[test]
    fn serialization() {
        let uri = SovereignUri::new(UriScheme::Agent, "agent-1");
        let desc = CapabilityDescriptor::new(uri, "analysis")
            .with_accuracy(0.9)
            .with_description("Data analysis capability");

        let json = serde_json::to_string_pretty(&desc).unwrap();
        assert!(json.contains("analysis"));
        assert!(json.contains("0.9"));
    }
}
