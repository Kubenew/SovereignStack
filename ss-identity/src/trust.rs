//! Trust profiles and reputation tracking.
//!
//! Implements the Agent Reputation Layer (Future Layer #17)
//! and Trust Framework.

use serde::{Deserialize, Serialize};
use ss_core::timestamp::Timestamp;
use ss_core::uri::SovereignUri;

/// A trust profile for an identity.
///
/// Trust is not boolean — it is a multi-dimensional score that evolves
/// over time based on observed behavior. Trust profiles are used for
/// routing decisions, federation policies, and capability matching.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustProfile {
    /// The identity this profile belongs to.
    pub identity: SovereignUri,
    /// Overall trust score (0.0 to 1.0).
    pub trust_score: f64,
    /// Historical accuracy of outputs.
    pub accuracy: f64,
    /// Reliability (uptime, completion rate).
    pub reliability: f64,
    /// Average response latency in milliseconds.
    pub latency_ms: u64,
    /// Average cost per operation.
    pub cost: f64,
    /// Number of completed interactions.
    pub interactions: u64,
    /// When this profile was last updated.
    pub updated_at: Timestamp,
    /// History of trust-affecting events.
    pub history: Vec<TrustEvent>,
}

impl TrustProfile {
    /// Create a new trust profile with default scores.
    pub fn new(identity: SovereignUri) -> Self {
        Self {
            identity,
            trust_score: 0.5, // Start neutral
            accuracy: 0.0,
            reliability: 0.0,
            latency_ms: 0,
            cost: 0.0,
            interactions: 0,
            updated_at: Timestamp::now(),
            history: Vec::new(),
        }
    }

    /// Record a successful interaction.
    pub fn record_success(&mut self, latency_ms: u64) {
        self.interactions += 1;
        self.update_accuracy(1.0);
        self.update_reliability(1.0);
        self.update_latency(latency_ms);
        self.updated_at = Timestamp::now();
        self.history.push(TrustEvent {
            timestamp: Timestamp::now(),
            event_type: TrustEventType::Success,
            impact: 0.01,
        });
        self.recompute_trust();
    }

    /// Record a failed interaction.
    pub fn record_failure(&mut self) {
        self.interactions += 1;
        self.update_accuracy(0.0);
        self.update_reliability(0.0);
        self.updated_at = Timestamp::now();
        self.history.push(TrustEvent {
            timestamp: Timestamp::now(),
            event_type: TrustEventType::Failure,
            impact: -0.05,
        });
        self.recompute_trust();
    }

    /// Check if the trust score meets a minimum threshold.
    pub fn meets_threshold(&self, threshold: f64) -> bool {
        self.trust_score >= threshold
    }

    fn update_accuracy(&mut self, outcome: f64) {
        if self.interactions == 1 {
            self.accuracy = outcome;
        } else {
            // Exponential moving average
            let alpha = 0.1;
            self.accuracy = alpha * outcome + (1.0 - alpha) * self.accuracy;
        }
    }

    fn update_reliability(&mut self, outcome: f64) {
        if self.interactions == 1 {
            self.reliability = outcome;
        } else {
            let alpha = 0.1;
            self.reliability = alpha * outcome + (1.0 - alpha) * self.reliability;
        }
    }

    fn update_latency(&mut self, new_latency: u64) {
        if self.interactions == 1 {
            self.latency_ms = new_latency;
        } else {
            // Running average
            self.latency_ms = (self.latency_ms * (self.interactions - 1) + new_latency)
                / self.interactions;
        }
    }

    fn recompute_trust(&mut self) {
        // Weighted combination of factors
        self.trust_score = (self.accuracy * 0.4
            + self.reliability * 0.3
            + (1.0 - (self.latency_ms as f64 / 10000.0).min(1.0)) * 0.2
            + (self.interactions.min(100) as f64 / 100.0) * 0.1)
            .clamp(0.0, 1.0);
    }
}

/// An event that affects trust.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustEvent {
    /// When this event occurred.
    pub timestamp: Timestamp,
    /// Type of event.
    pub event_type: TrustEventType,
    /// Impact on trust score (-1.0 to 1.0).
    pub impact: f64,
}

/// Types of trust-affecting events.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TrustEventType {
    /// Successful task completion.
    Success,
    /// Failed task.
    Failure,
    /// Verification by another trusted agent.
    Verification,
    /// Policy violation.
    Violation,
    /// Manual trust adjustment.
    Manual,
}

#[cfg(test)]
mod tests {
    use super::*;
    use ss_core::uri::{SovereignUri, UriScheme};

    #[test]
    fn new_profile_starts_neutral() {
        let uri = SovereignUri::new(UriScheme::Agent, "test");
        let profile = TrustProfile::new(uri);
        assert_eq!(profile.trust_score, 0.5);
        assert_eq!(profile.interactions, 0);
    }

    #[test]
    fn success_increases_trust() {
        let uri = SovereignUri::new(UriScheme::Agent, "test");
        let mut profile = TrustProfile::new(uri);
        let initial_trust = profile.trust_score;

        profile.record_success(100);
        assert!(profile.trust_score > initial_trust);
        assert_eq!(profile.interactions, 1);
    }

    #[test]
    fn failure_tracked() {
        let uri = SovereignUri::new(UriScheme::Agent, "test");
        let mut profile = TrustProfile::new(uri);

        profile.record_failure();
        assert_eq!(profile.interactions, 1);
        assert!(profile.history.len() == 1);
    }

    #[test]
    fn trust_threshold() {
        let uri = SovereignUri::new(UriScheme::Agent, "test");
        let mut profile = TrustProfile::new(uri);

        // Build up trust through successes
        for _ in 0..20 {
            profile.record_success(50);
        }

        assert!(profile.meets_threshold(0.3));
    }
}
