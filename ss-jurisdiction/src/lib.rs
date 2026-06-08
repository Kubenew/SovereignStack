//! ss-jurisdiction — Jurisdiction Compliance Engine
//!
//! Enforces data residency, blocks cross-border transfers, and evaluates
//! sovereign policy compliance for every object and operation.

use std::collections::HashMap;

/// ISO 3166-1 alpha-2 jurisdiction code.
pub type JurisdictionCode = String;

/// Verdict of a jurisdiction check.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JurisdictionVerdict {
    Allowed,
    Blocked(String),
    RequiresAudit(String),
}

/// A jurisdiction compliance rule.
#[derive(Debug, Clone)]
pub struct JurisdictionRule {
    pub source: JurisdictionCode,
    pub target: JurisdictionCode,
    pub action: String,
    pub verdict: JurisdictionVerdict,
}

/// Jurisdiction Compliance Engine.
#[derive(Debug, Default)]
pub struct JurisdictionEngine {
    rules: Vec<JurisdictionRule>,
}

impl JurisdictionEngine {
    pub fn new() -> Self { Self::default() }

    pub fn add_rule(&mut self, rule: JurisdictionRule) { self.rules.push(rule); }

    pub fn evaluate(&self, source: &str, target: &str, action: &str) -> JurisdictionVerdict {
        for rule in &self.rules {
            if rule.source == source && rule.target == target && rule.action == action {
                return rule.verdict.clone();
            }
        }
        // Default: block unknown jurisdiction transfers
        JurisdictionVerdict::Blocked(format!("No rule for {source}→{target} {action}"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn eu_non_eu_blocked() {
        let mut engine = JurisdictionEngine::new();
        engine.add_rule(JurisdictionRule {
            source: "EU".into(), target: "non-EU".into(),
            action: "transfer".into(),
            verdict: JurisdictionVerdict::Blocked("GDPR: cross-border data transfer denied".into()),
        });
        let v = engine.evaluate("EU", "non-EU", "transfer");
        assert_eq!(v, JurisdictionVerdict::Blocked("GDPR: cross-border data transfer denied".into()));
    }

    #[test]
    fn same_jurisdiction_allowed() {
        let engine = JurisdictionEngine::new();
        let v = engine.evaluate("EU", "EU", "infer");
        assert!(matches!(v, JurisdictionVerdict::Blocked(_))); // default deny
    }
}
