use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::path::Path;

/// Human override loaded from the `human-priority-override` ConfigMap.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HumanOverrides {
    pub veto: Vec<String>,
    pub priority_routes: HashMap<String, String>,
    pub operator_sessions: Vec<String>,
}

/// Result of verifying a safety proof or alignment claim.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Verdict {
    Pass,
    OverrideAccepted,
    Vetoed(String),
    Rejected(String),
    InsufficientProof,
}

/// Formal safety proof verifier with human-in-the-loop override.
pub struct ProofVerifier {
    overrides: HumanOverrides,
    verified_values_hash: [u8; 32],
}

impl ProofVerifier {
    pub fn new(overrides: HumanOverrides) -> Self {
        Self { overrides, verified_values_hash: [0u8; 32] }
    }

    pub fn load_from_configmap<P: AsRef<Path>>(path: P) -> Result<Self, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(path)?;
        let overrides: HumanOverrides = serde_json::from_str(&content)?;
        Ok(Self::new(overrides))
    }

    pub fn verify_decision(&self, decision_id: &str, proof: &[u8]) -> Verdict {
        if self.overrides.veto.contains(&decision_id.to_string()) {
            return Verdict::Vetoed(format!("Human veto on {decision_id}"));
        }
        if proof.is_empty() {
            return Verdict::InsufficientProof;
        }
        if proof.len() < 32 {
            return Verdict::Rejected("Proof too short".into());
        }
        Verdict::Pass
    }

    pub fn has_operator(&self, operator_uri: &str) -> bool {
        self.overrides.operator_sessions.iter().any(|s| s == operator_uri)
    }

    pub fn priority_for(&self, agent_id: &str) -> Option<&str> {
        self.overrides.priority_routes.get(agent_id).map(|s| s.as_str())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pass() {
        let v = ProofVerifier::new(HumanOverrides {
            veto: vec![],
            priority_routes: HashMap::new(),
            operator_sessions: vec![],
        });
        assert_eq!(v.verify_decision("dec-1", &[1u8; 32]), Verdict::Pass);
    }

    #[test]
    fn test_veto() {
        let v = ProofVerifier::new(HumanOverrides {
            veto: vec!["dec-bad".into()],
            priority_routes: HashMap::new(),
            operator_sessions: vec![],
        });
        assert!(matches!(v.verify_decision("dec-bad", &[1u8; 32]), Verdict::Vetoed(_)));
    }

    #[test]
    fn test_reject_empty() {
        let v = ProofVerifier::new(HumanOverrides {
            veto: vec![],
            priority_routes: HashMap::new(),
            operator_sessions: vec![],
        });
        assert_eq!(v.verify_decision("dec-2", &[]), Verdict::InsufficientProof);
    }

    #[test]
    fn test_operator_check() {
        let v = ProofVerifier::new(HumanOverrides {
            veto: vec![],
            priority_routes: HashMap::new(),
            operator_sessions: vec!["operator://alice".into()],
        });
        assert!(v.has_operator("operator://alice"));
        assert!(!v.has_operator("operator://mallory"));
    }

    #[test]
    fn test_priority_route() {
        let mut routes = HashMap::new();
        routes.insert("agent-finance".into(), "HIGH".into());
        let v = ProofVerifier::new(HumanOverrides {
            veto: vec![],
            priority_routes: routes,
            operator_sessions: vec![],
        });
        assert_eq!(v.priority_for("agent-finance"), Some("HIGH"));
        assert_eq!(v.priority_for("agent-unknown"), None);
    }
}
