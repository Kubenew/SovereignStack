//! Policy Engine — evaluate governance policies against operations.

use ss_core::SovereignUri;
use std::sync::Arc;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Policy {
    pub uri: SovereignUri,
    pub version: String,
    pub jurisdiction: Option<String>,
    pub rules: Vec<PolicyRule>,
    pub enforcement: EnforcementLevel,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PolicyRule {
    pub effect: RuleEffect,
    pub action: String,
    pub resource: String,
    pub condition: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum RuleEffect {
    Allow,
    Deny,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum EnforcementLevel {
    Hard,
    Soft,
    AuditOnly,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PolicyDecision {
    pub allowed: bool,
    pub policy: SovereignUri,
    pub rule: Option<String>,
    pub reason: String,
}

pub trait PolicyEngine: Send + Sync {
    fn add_policy(&self, policy: Policy);
    fn remove_policy(&self, uri: &SovereignUri);
    fn evaluate(&self, action: &str, resource: &SovereignUri, context: &PolicyContext) -> PolicyDecision;
    fn list_policies(&self) -> Vec<Policy>;
}

#[derive(Debug, Clone)]
pub struct PolicyContext {
    pub caller: SovereignUri,
    pub jurisdiction: Option<String>,
    pub target_jurisdiction: Option<String>,
}

pub struct PolicyEngineImpl {
    policies: Arc<dashmap::DashMap<String, Policy>>,
}

impl PolicyEngineImpl {
    pub fn new() -> Self {
        Self {
            policies: Arc::new(dashmap::DashMap::new()),
        }
    }
}

impl PolicyEngine for PolicyEngineImpl {
    fn add_policy(&self, policy: Policy) {
        self.policies.insert(policy.uri.to_string(), policy);
    }

    fn remove_policy(&self, uri: &SovereignUri) {
        self.policies.remove(&uri.to_string());
    }

    fn evaluate(&self, action: &str, _resource: &SovereignUri, _context: &PolicyContext) -> PolicyDecision {
        for entry in self.policies.iter() {
            let policy = entry.value();
            for rule in &policy.rules {
                if rule.action == action {
                    return PolicyDecision {
                        allowed: matches!(rule.effect, RuleEffect::Allow),
                        policy: policy.uri.clone(),
                        rule: Some(format!("{:?}", rule.effect)),
                        reason: format!("policy {} rule matched action {}", policy.uri, action),
                    };
                }
            }
        }
        PolicyDecision {
            allowed: true,
            policy: SovereignUri::new("policy://default"),
            rule: None,
            reason: "no matching policy, default allow".into(),
        }
    }

    fn list_policies(&self) -> Vec<Policy> {
        self.policies.iter().map(|e| e.value().clone()).collect()
    }
}
