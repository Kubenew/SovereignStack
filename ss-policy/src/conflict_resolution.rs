//! # RFC-0075: Policy Conflict Resolution
//!
//! Implements the RFC-0075 conflict taxonomy (Types A-E), the deterministic
//! resolution hierarchy (Hard Supremacy -> Explicit Precedence -> Specificity
//! -> Temporal -> Delegation Chain -> Escalation), the safe-halt default, and
//! the `conflict://` evidence object.
//!
//! Default for any unresolved conflict is **safe halt + human escalation**,
//! never a guess.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashSet};

/// Jurisdiction to which a policy belongs.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Jurisdiction(pub String);

/// Scope predicate: which subjects/capabilities/resources a policy governs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Scope {
    pub subjects: HashSet<String>,
    pub capabilities: HashSet<String>,
    pub resources: HashSet<String>,
}

impl Scope {
    /// Whether `value` matches any scope entry; a trailing `*` acts as a
    /// prefix wildcard (e.g. `agent://*` matches `agent://treasury`).
    pub fn matches(&self, subject: &str, capability: &str, resource: &str) -> bool {
        Self::entry_matches(&self.subjects, subject)
            && Self::entry_matches(&self.capabilities, capability)
            && Self::entry_matches(&self.resources, resource)
    }

    fn entry_matches(set: &HashSet<String>, value: &str) -> bool {
        set.iter().any(|pattern| {
            pattern
                .strip_suffix('*')
                .map_or_else(|| pattern == value, |prefix| value.starts_with(prefix))
        })
    }

    /// Number of exact (non-wildcard) entries — used for specificity ranking.
    fn exact_count(set: &HashSet<String>) -> usize {
        set.iter().filter(|pattern| !pattern.ends_with('*')).count()
    }
}

/// Supremacy class of a policy (RFC-0075 Section 4.1).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SupremacyClass {
    /// Constitutional / legal minimum. Always wins.
    Hard,
    /// Ordinary policy. Loses to Hard.
    Normal,
}

/// A single applicable policy.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Policy {
    /// Stable address, e.g. `policy://org/acceptable-use`.
    pub id: String,
    pub jurisdiction: Jurisdiction,
    pub scope: Scope,
    pub supremacy: SupremacyClass,
    /// Explicit `precedes` declarations from a trusted authority (RFC-0075 §4.2).
    pub precedes: Vec<String>,
    /// Optional explicit precedence key.
    pub precedence_key: Option<u64>,
    /// Enactment timestamp (RFC-0075 §4.4).
    pub enacted_at: i64,
    /// End of validity (None = evergreen).
    pub sunsets_at: Option<i64>,
    /// Delegation depth: 0 = principal-owned, >0 = delegated further out.
    pub delegation_depth: u32,
    /// The intended decision for the action under evaluation.
    pub decision: Decision,
}

/// What a policy says about the action.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Decision {
    Permit,
    Deny,
}

/// Conflict taxonomy (RFC-0075 Section 3).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ConflictType {
    /// Effect Contradiction — two policies require mutually exclusive outcomes.
    EffectContradiction,
    /// Obligation Collision — two policies impose incompatible duties.
    ObligationCollision,
    /// Scope Ambiguity — overlapping scopes, not strictly ordered.
    ScopeAmbiguity,
    /// Capability Inconsistency — disagreement on whether actor may hold a capability.
    CapabilityInconsistency,
    /// Temporal Conflict — individually valid but contradictory in time.
    TemporalConflict,
}

/// Outcome of evaluating a single action.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvaluationOutcome {
    /// All applicable policies agree.
    Authorized,
    /// All applicable policies agree on denial.
    Denied,
    /// No applicable policies (permitted by absence of governance).
    NoPolicy,
    /// Conflicting policies, resolved by the hierarchy.
    Resolved {
        decision: Decision,
        rule: ResolutionRule,
    },
    /// Conflicting policies, unresolvable: safe halt + human escalation.
    Escalated { evidence: ConflictEvidence },
}

/// Resolution rule applied by the hierarchy (RFC-0075 Section 4).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ResolutionRule {
    HardSupremacy,
    ExplicitPrecedence,
    Specificity,
    Temporal,
    DelegationChain,
}

/// The `conflict://` evidence object (RFC-0075 Section 6).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConflictEvidence {
    pub action: String,
    pub policies: Vec<String>,
    pub conflict_type: ConflictType,
    pub resolution: Option<ResolutionRule>,
    pub decision: Option<Decision>,
    pub human_override: Option<String>,
    pub parent: Option<String>,
    pub signature: String,
}

/// The Conflict Resolution Service (RFC-0075 Section 7).
#[derive(Debug, Default)]
pub struct ConflictResolutionService {
    /// Hard-supremacy invariants defined in the platform constitution.
    constitutional_invariants: Vec<String>,
}

impl ConflictResolutionService {
    pub fn new() -> Self {
        Self::default()
    }

    /// Register a constitutional hard-supremacy invariant.
    pub fn add_constitutional_invariant(&mut self, policy_id: impl Into<String>) {
        self.constitutional_invariants.push(policy_id.into());
    }

    /// Compute the applicable policy set `P(A)`.
    pub fn applicable<'a>(
        &self,
        policies: &'a [Policy],
        subject: &str,
        capability: &str,
        resource: &str,
        at: i64,
    ) -> Vec<&'a Policy> {
        policies
            .iter()
            .filter(|p| {
                p.scope.matches(subject, capability, resource)
                    && p.enacted_at <= at
                    && p.sunsets_at.map_or(true, |s| s >= at)
            })
            .collect()
    }

    /// Evaluate an action across its applicable policy set.
    pub fn evaluate(
        &self,
        policies: &[Policy],
        subject: &str,
        capability: &str,
        resource: &str,
        at: i64,
    ) -> EvaluationOutcome {
        let applicable = self.applicable(policies, subject, capability, resource, at);
        if applicable.is_empty() {
            return EvaluationOutcome::NoPolicy;
        }

        let permits: Vec<&Policy> = applicable
            .iter()
            .copied()
            .filter(|p| p.decision == Decision::Permit)
            .collect();
        let denies: Vec<&Policy> = applicable
            .iter()
            .copied()
            .filter(|p| p.decision == Decision::Deny)
            .collect();

        // If all policies agree, no conflict exists.
        if permits.is_empty() {
            return EvaluationOutcome::Denied;
        }
        if denies.is_empty() {
            return EvaluationOutcome::Authorized;
        }

        // Hard supremacy: a Hard policy always wins.
        let hard = applicable.iter().copied().find(|p| {
            p.supremacy == SupremacyClass::Hard
                || self.constitutional_invariants.contains(&p.id)
        });
        if let Some(h) = hard {
            return EvaluationOutcome::Resolved {
                decision: h.decision,
                rule: ResolutionRule::HardSupremacy,
            };
        }

        // Explicit precedence: a mutually trusted authority declared `precedes`.
        for p in &denies {
            if permits.iter().any(|q| p.precedes.contains(&q.id)) {
                return EvaluationOutcome::Resolved {
                    decision: Decision::Deny,
                    rule: ResolutionRule::ExplicitPrecedence,
                };
            }
        }
        for p in &permits {
            if denies.iter().any(|q| p.precedes.contains(&q.id)) {
                return EvaluationOutcome::Resolved {
                    decision: Decision::Permit,
                    rule: ResolutionRule::ExplicitPrecedence,
                };
            }
        }

        // Explicit precedence key: the lowest key wins when set (RFC-0075 §4.2).
        if let Some(preceder) = Self::unique_winner(
            &applicable,
            |p| p.precedence_key.unwrap_or(u64::MAX),
            true,
        ) {
            if preceder.precedence_key.is_some() {
                return EvaluationOutcome::Resolved {
                    decision: preceder.decision,
                    rule: ResolutionRule::ExplicitPrecedence,
                };
            }
        }

        // Specificity: the policy with the most specific scope governs — but
        // only when a strict unique winner exists. Ties fall through.
        if let Some(specific) = Self::unique_winner(
            &applicable,
            |p| Scope::exact_count(&p.scope.subjects)
                + Scope::exact_count(&p.scope.capabilities)
                + Scope::exact_count(&p.scope.resources),
            false,
        ) {
            return EvaluationOutcome::Resolved {
                decision: specific.decision,
                rule: ResolutionRule::Specificity,
            };
        }

        // Temporal: the later-enacted policy governs (sunset-aware), unique only.
        if let Some(latest) = Self::unique_winner(&applicable, |p| p.enacted_at, false) {
            return EvaluationOutcome::Resolved {
                decision: latest.decision,
                rule: ResolutionRule::Temporal,
            };
        }

        // Delegation chain: prefer the policy closest to the principal, unique only.
        if let Some(closest) = Self::unique_winner(&applicable, |p| p.delegation_depth, true) {
            return EvaluationOutcome::Resolved {
                decision: closest.decision,
                rule: ResolutionRule::DelegationChain,
            };
        }

        // Unresolved: safe halt + human escalation. No guessing.
        let conflict_type = permits
            .first()
            .zip(denies.first())
            .map(|(p, d)| classify(p, d))
            .unwrap_or(ConflictType::ScopeAmbiguity);
        let evidence = self.build_evidence(
            subject,
            &applicable.iter().map(|p| p.id.clone()).collect::<Vec<_>>(),
            conflict_type,
        );
        EvaluationOutcome::Escalated { evidence }
    }

    /// Return the unique policy winning on `key` (max, or min when
    /// `prefer_smallest` is true). Returns `None` on ties so the evaluation
    /// falls through to the next hierarchy rule instead of guessing.
    fn unique_winner<'a, K, F>(
        policies: &[&'a Policy],
        key: F,
        prefer_smallest: bool,
    ) -> Option<&'a Policy>
    where
        K: Ord,
        F: Fn(&Policy) -> K,
    {
        if policies.is_empty() {
            return None;
        }
        let mut best = policies[0];
        let mut best_key = key(best);
        let mut tied = false;
        for p in &policies[1..] {
            let p = *p;
            let k = key(p);
            let better = if prefer_smallest { k < best_key } else { k > best_key };
            if k == best_key {
                tied = true;
            } else if better {
                best = p;
                best_key = k;
                tied = false;
            }
        }
        if tied {
            None
        } else {
            Some(best)
        }
    }

    fn build_evidence(
        &self,
        action: &str,
        policy_ids: &[String],
        conflict_type: ConflictType,
    ) -> ConflictEvidence {
        let mut sorted: Vec<String> = policy_ids.to_vec();
        sorted.sort();
        let mut hasher = Sha256::new();
        hasher.update(b"conflict://");
        hasher.update(action.as_bytes());
        for id in &sorted {
            hasher.update(id.as_bytes());
            hasher.update(&[0u8]);
        }
        let digest = hasher.finalize();
        let signature = hex::encode(digest);
        ConflictEvidence {
            action: action.to_string(),
            policies: sorted,
            conflict_type,
            resolution: None,
            decision: None,
            human_override: None,
            parent: None,
            signature,
        }
    }
}

/// Deterministic conflict classification of a policy pair (RFC-0075 §3).
pub fn classify(a: &Policy, b: &Policy) -> ConflictType {
    if a.scope == b.scope && a.jurisdiction != b.jurisdiction {
        // Both authorities claim governance of the identical scope -> C.
        ConflictType::ScopeAmbiguity
    } else if a.jurisdiction == b.jurisdiction && a.decision != b.decision {
        // Same jurisdiction, incompatible duties -> B.
        ConflictType::ObligationCollision
    } else if a.decision != b.decision {
        // Different jurisdictions, mutually exclusive outcomes -> A.
        ConflictType::EffectContradiction
    } else if a.scope.subjects == b.scope.subjects {
        // Disagreement over whether the actor may hold the capability -> D.
        ConflictType::CapabilityInconsistency
    } else {
        ConflictType::TemporalConflict
    }
}

/// Render a conflict evidence object as a stable map (for serialization/audit).
pub fn evidence_as_map(evidence: &ConflictEvidence) -> BTreeMap<String, String> {
    let mut m = BTreeMap::new();
    m.insert("action".into(), evidence.action.clone());
    m.insert(
        "policies".into(),
        serde_json::to_string(&evidence.policies).unwrap_or_default(),
    );
    m.insert(
        "conflict_type".into(),
        format!("{:?}", evidence.conflict_type),
    );
    m.insert(
        "resolution".into(),
        evidence
            .resolution
            .map(|r| format!("{:?}", r))
            .unwrap_or_else(|| "escalated".into()),
    );
    m.insert(
        "decision".into(),
        evidence
            .decision
            .map(|d| format!("{:?}", d))
            .unwrap_or_else(|| "none".into()),
    );
    m.insert(
        "human_override".into(),
        evidence.human_override.clone().unwrap_or_default(),
    );
    m.insert("parent".into(), evidence.parent.clone().unwrap_or_default());
    m.insert("signature".into(), evidence.signature.clone());
    m
}

#[cfg(test)]
mod tests {
    use super::*;

    fn policy(
        id: &str,
        jurisdiction: &str,
        subjects: &[&str],
        capabilities: &[&str],
        resources: &[&str],
        supremacy: SupremacyClass,
        decision: Decision,
        enacted_at: i64,
    ) -> Policy {
        Policy {
            id: id.to_string(),
            jurisdiction: Jurisdiction(jurisdiction.to_string()),
            scope: Scope {
                subjects: subjects.iter().map(|s| s.to_string()).collect(),
                capabilities: capabilities.iter().map(|s| s.to_string()).collect(),
                resources: resources.iter().map(|s| s.to_string()).collect(),
            },
            supremacy,
            precedes: vec![],
            precedence_key: None,
            enacted_at,
            sunsets_at: None,
            delegation_depth: 0,
            decision,
        }
    }

    #[test]
    fn test_authorized_all_permit() {
        let svc = ConflictResolutionService::new();
        let policies = vec![
            policy("org", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100),
            policy("jur", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100),
        ];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Authorized
        );
    }

    #[test]
    fn test_denied_all_deny() {
        let svc = ConflictResolutionService::new();
        let policies = vec![
            policy("org", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100),
            policy("jur", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100),
        ];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Denied
        );
    }

    #[test]
    fn test_no_policy() {
        let svc = ConflictResolutionService::new();
        let policies = vec![policy(
            "org",
            "EU",
            &["agent://other"],
            &["transfer"],
            &["usd"],
            SupremacyClass::Normal,
            Decision::Permit,
            100,
        )];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::NoPolicy
        );
    }

    #[test]
    fn test_hard_supremacy_wins() {
        let svc = ConflictResolutionService::new();
        let policies = vec![
            policy("org", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100),
            policy("constitution", "GLOBAL", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Hard, Decision::Deny, 0),
        ];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Deny,
                rule: ResolutionRule::HardSupremacy,
            }
        );
    }

    #[test]
    fn test_constitutional_invariant_via_registry() {
        let mut svc = ConflictResolutionService::new();
        svc.add_constitutional_invariant("policy://system/zero-exfiltration");
        let policies = vec![
            policy("org", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100),
            policy("system", "GLOBAL", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 0),
        ];
        // The system policy id is registered as a constitutional invariant.
        let mut p = policies[1].clone();
        p.id = "policy://system/zero-exfiltration".to_string();
        let policies = vec![policies[0].clone(), p];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Deny,
                rule: ResolutionRule::HardSupremacy,
            }
        );
    }

    #[test]
    fn test_explicit_precedence() {
        let svc = ConflictResolutionService::new();
        let mut jur = policy("policy://jur/eu", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        jur.precedes = vec!["policy://org/allow".to_string()];
        let policies = vec![
            policy("policy://org/allow", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100),
            jur,
        ];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Deny,
                rule: ResolutionRule::ExplicitPrecedence,
            }
        );
    }

    #[test]
    fn test_precedence_key() {
        let svc = ConflictResolutionService::new();
        let mut org = policy("org", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100);
        org.precedence_key = Some(10);
        let mut jur = policy("jur", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        jur.precedence_key = Some(5); // lower key wins
        assert_eq!(
            svc.evaluate(&[org, jur], "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Deny,
                rule: ResolutionRule::ExplicitPrecedence,
            }
        );
    }

    #[test]
    fn test_specificity() {
        let svc = ConflictResolutionService::new();
        // Broad policy permits, specific policy denies -> specific governs.
        let broad = policy("org", "EU", &["agent://*"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100);
        let specific = policy(
            "org-specific",
            "EU",
            &["agent://treasury"],
            &["transfer"],
            &["usd"],
            SupremacyClass::Normal,
            Decision::Deny,
            100,
        );
        assert_eq!(
            svc.evaluate(&[broad, specific], "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Deny,
                rule: ResolutionRule::Specificity,
            }
        );
    }

    #[test]
    fn test_temporal_later_wins() {
        let svc = ConflictResolutionService::new();
        let policies = vec![
            policy("old", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100),
            policy("new", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 300),
        ];
        assert_eq!(
            svc.evaluate(&policies, "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Deny,
                rule: ResolutionRule::Temporal,
            }
        );
    }

    #[test]
    fn test_delegation_chain_closest_to_principal() {
        let svc = ConflictResolutionService::new();
        let mut principal = policy("principal", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100);
        principal.delegation_depth = 0;
        let mut broker = policy("broker", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        broker.delegation_depth = 2;
        assert_eq!(
            svc.evaluate(&[principal, broker], "agent://treasury", "transfer", "usd", 200),
            EvaluationOutcome::Resolved {
                decision: Decision::Permit,
                rule: ResolutionRule::DelegationChain,
            }
        );
    }

    #[test]
    fn test_safe_halt_escalation_on_unresolved() {
        let svc = ConflictResolutionService::new();
        // Identical scopes, same supremacy, same enactment, no precedence, no
        // specificity difference, same delegation depth -> unresolved.
        let a = policy("a", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100);
        let b = policy("b", "US", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        let outcome = svc.evaluate(&[a, b], "agent://treasury", "transfer", "usd", 200);
        match outcome {
            EvaluationOutcome::Escalated { evidence } => {
                assert!(evidence.policies.contains(&"a".to_string()));
                assert!(evidence.policies.contains(&"b".to_string()));
                assert_eq!(evidence.resolution, None);
                assert!(!evidence.signature.is_empty());
            }
            other => panic!("expected Escalated, got {other:?}"),
        }
    }

    #[test]
    fn test_evidence_signature_is_deterministic() {
        let svc = ConflictResolutionService::new();
        let a = policy("a", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100);
        let b = policy("b", "US", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        let (e1, e2) = match (
            svc.evaluate(&[a.clone(), b.clone()], "agent://treasury", "transfer", "usd", 200),
            svc.evaluate(&[a, b], "agent://treasury", "transfer", "usd", 200),
        ) {
            (EvaluationOutcome::Escalated { evidence: e1 }, EvaluationOutcome::Escalated { evidence: e2 }) => (e1, e2),
            _ => panic!("expected escalations"),
        };
        assert_eq!(e1.signature, e2.signature);
    }

    #[test]
    fn test_classify_taxonomy() {
        let eu = policy("a", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Permit, 100);
        let us = policy("b", "US", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        assert_eq!(
            classify(&eu, &us),
            ConflictType::ScopeAmbiguity
        );
        let eu2 = policy("c", "EU", &["agent://treasury"], &["transfer"], &["usd"], SupremacyClass::Normal, Decision::Deny, 100);
        assert_eq!(
            classify(&eu, &eu2),
            ConflictType::ObligationCollision
        );
    }
}
