//! Capability queries — how agents request capabilities from the network.

use serde::{Deserialize, Serialize};

use crate::descriptor::CapabilityDescriptor;

/// A query for a specific capability.
///
/// Instead of addressing a specific agent, agents query the network
/// for a required capability. The network finds the best matching
/// providers.
///
/// # Example
///
/// ```rust
/// use ss_capability::CapabilityQuery;
///
/// let query = CapabilityQuery::new("legal_review")
///     .with_language("cs")
///     .with_jurisdiction("EU")
///     .with_min_accuracy(0.9)
///     .with_max_cost(1.0)
///     .with_max_latency_ms(5000);
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityQuery {
    /// Required capability name.
    pub capability: String,
    /// Required language (optional).
    pub language: Option<String>,
    /// Required jurisdiction (optional).
    pub jurisdiction: Option<String>,
    /// Minimum acceptable accuracy.
    pub min_accuracy: Option<f64>,
    /// Maximum acceptable cost.
    pub max_cost: Option<f64>,
    /// Maximum acceptable latency in ms.
    pub max_latency_ms: Option<u64>,
    /// Required tags (all must match).
    pub required_tags: Vec<String>,
    /// Maximum number of results to return.
    pub max_results: usize,
}

impl CapabilityQuery {
    /// Create a new query for a capability.
    pub fn new(capability: &str) -> Self {
        Self {
            capability: capability.to_string(),
            language: None,
            jurisdiction: None,
            min_accuracy: None,
            max_cost: None,
            max_latency_ms: None,
            required_tags: Vec::new(),
            max_results: 10,
        }
    }

    /// Require a specific language.
    pub fn with_language(mut self, lang: &str) -> Self {
        self.language = Some(lang.to_string());
        self
    }

    /// Require a specific jurisdiction.
    pub fn with_jurisdiction(mut self, jurisdiction: &str) -> Self {
        self.jurisdiction = Some(jurisdiction.to_string());
        self
    }

    /// Set minimum accuracy threshold.
    pub fn with_min_accuracy(mut self, accuracy: f64) -> Self {
        self.min_accuracy = Some(accuracy);
        self
    }

    /// Set maximum cost threshold.
    pub fn with_max_cost(mut self, cost: f64) -> Self {
        self.max_cost = Some(cost);
        self
    }

    /// Set maximum latency threshold.
    pub fn with_max_latency_ms(mut self, latency: u64) -> Self {
        self.max_latency_ms = Some(latency);
        self
    }

    /// Require specific tags.
    pub fn with_tags(mut self, tags: Vec<String>) -> Self {
        self.required_tags = tags;
        self
    }

    /// Set max results.
    pub fn with_max_results(mut self, max: usize) -> Self {
        self.max_results = max;
        self
    }

    /// Check if a descriptor matches this query.
    pub fn matches(&self, descriptor: &CapabilityDescriptor) -> bool {
        // Must match capability name
        if descriptor.capability != self.capability {
            return false;
        }

        // Must be available
        if !descriptor.available {
            return false;
        }

        // Check language
        if let Some(ref lang) = self.language {
            if !descriptor.supports_language(lang) {
                return false;
            }
        }

        // Check jurisdiction
        if let Some(ref jurisdiction) = self.jurisdiction {
            if !descriptor.supports_jurisdiction(jurisdiction) {
                return false;
            }
        }

        // Check accuracy threshold
        if let Some(min_acc) = self.min_accuracy {
            if descriptor.accuracy < min_acc {
                return false;
            }
        }

        // Check cost threshold
        if let Some(max_cost) = self.max_cost {
            if descriptor.cost > max_cost {
                return false;
            }
        }

        // Check latency threshold
        if let Some(max_lat) = self.max_latency_ms {
            if descriptor.latency_ms > max_lat {
                return false;
            }
        }

        // Check required tags
        for tag in &self.required_tags {
            if !descriptor.tags.iter().any(|t| t == tag) {
                return false;
            }
        }

        true
    }
}

/// The result of a capability query.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityMatch {
    /// The matching descriptor.
    pub descriptor: CapabilityDescriptor,
    /// Relevance score (higher = better match).
    pub score: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use ss_core::uri::{SovereignUri, UriScheme};

    fn make_descriptor(name: &str, capability: &str) -> CapabilityDescriptor {
        CapabilityDescriptor::new(
            SovereignUri::new(UriScheme::Agent, name),
            capability,
        )
    }

    #[test]
    fn basic_query_match() {
        let query = CapabilityQuery::new("analysis");
        let desc = make_descriptor("agent-1", "analysis");
        assert!(query.matches(&desc));
    }

    #[test]
    fn query_wrong_capability() {
        let query = CapabilityQuery::new("analysis");
        let desc = make_descriptor("agent-1", "coding");
        assert!(!query.matches(&desc));
    }

    #[test]
    fn query_with_accuracy_filter() {
        let query = CapabilityQuery::new("analysis").with_min_accuracy(0.9);

        let good = make_descriptor("agent-1", "analysis").with_accuracy(0.95);
        let bad = make_descriptor("agent-2", "analysis").with_accuracy(0.5);

        assert!(query.matches(&good));
        assert!(!query.matches(&bad));
    }

    #[test]
    fn query_with_cost_filter() {
        let query = CapabilityQuery::new("analysis").with_max_cost(1.0);

        let cheap = make_descriptor("agent-1", "analysis").with_cost(0.5);
        let expensive = make_descriptor("agent-2", "analysis").with_cost(5.0);

        assert!(query.matches(&cheap));
        assert!(!query.matches(&expensive));
    }

    #[test]
    fn query_with_language() {
        let query = CapabilityQuery::new("review").with_language("cs");

        let czech = make_descriptor("agent-1", "review")
            .with_languages(vec!["cs".to_string(), "en".to_string()]);
        let english_only = make_descriptor("agent-2", "review")
            .with_languages(vec!["en".to_string()]);

        assert!(query.matches(&czech));
        assert!(!query.matches(&english_only));
    }

    #[test]
    fn query_serialization() {
        let query = CapabilityQuery::new("legal_review")
            .with_language("cs")
            .with_jurisdiction("EU")
            .with_min_accuracy(0.9);

        let json = serde_json::to_string_pretty(&query).unwrap();
        assert!(json.contains("legal_review"));
        assert!(json.contains("cs"));
        assert!(json.contains("EU"));
    }
}
