//! Common types shared across SovereignStack subsystems.

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::fmt;

use crate::timestamp::Timestamp;
use crate::uri::SovereignUri;

/// A unique identifier for any SovereignStack object.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ObjectId(Uuid);

impl ObjectId {
    /// Generate a new random ObjectId.
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    /// Create from an existing UUID.
    pub fn from_uuid(uuid: Uuid) -> Self {
        Self(uuid)
    }

    /// Returns the inner UUID.
    pub fn as_uuid(&self) -> &Uuid {
        &self.0
    }
}

impl Default for ObjectId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for ObjectId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Metadata attached to every SovereignStack object.
///
/// Ensures every object satisfies the seven core properties:
/// Identifiable, Addressable, Discoverable, Verifiable,
/// Portable, Federatable, Auditable.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectMeta {
    /// Unique identifier.
    pub id: ObjectId,
    /// Sovereign URI — the global address.
    pub uri: SovereignUri,
    /// Who created this object.
    pub created_by: SovereignUri,
    /// When this object was created.
    pub created_at: Timestamp,
    /// When this object was last modified.
    pub modified_at: Timestamp,
    /// Version number.
    pub version: u64,
    /// Optional human-readable description.
    pub description: Option<String>,
    /// Tags for discovery.
    pub tags: Vec<String>,
}

impl ObjectMeta {
    /// Create new metadata for an object.
    pub fn new(uri: SovereignUri, created_by: SovereignUri) -> Self {
        let now = Timestamp::now();
        Self {
            id: ObjectId::new(),
            uri,
            created_by,
            created_at: now,
            modified_at: now,
            version: 1,
            description: None,
            tags: Vec::new(),
        }
    }

    /// Add a description.
    pub fn with_description(mut self, desc: impl Into<String>) -> Self {
        self.description = Some(desc.into());
        self
    }

    /// Add tags for discovery.
    pub fn with_tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }

    /// Increment version and update modification time.
    pub fn bump_version(&mut self) {
        self.version += 1;
        self.modified_at = Timestamp::now();
    }
}

/// A single entry in an object's provenance chain.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceEntry {
    /// What action occurred (created, updated, derived, etc.)
    pub action: String,
    /// Agent or node that performed the action
    pub agent: SovereignUri,
    /// When the action occurred
    pub timestamp: Timestamp,
    /// Optional: previous version URI (for updates)
    pub previous: Option<String>,
    /// Optional: reason or justification
    pub reason: Option<String>,
}

/// Trust score for an identity or object (0–100).
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct TrustScore {
    pub value: u8,
}

impl TrustScore {
    pub fn new(value: u8) -> Self {
        Self { value: value.min(100) }
    }

    pub fn meets_threshold(&self, min: u8) -> bool {
        self.value >= min
    }
}

impl Default for TrustScore {
    fn default() -> Self {
        Self { value: 50 }
    }
}

/// A descriptor for a capability in the capability registry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityDescriptor {
    pub id: String,
    pub provider: SovereignUri,
    pub display_name: String,
    pub inputs: Vec<CapabilityParam>,
    pub outputs: Vec<CapabilityParam>,
    pub trust_required: u8,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityParam {
    pub name: String,
    pub param_type: String,
    pub required: bool,
}

/// A claim within a knowledge object.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeClaim {
    pub statement: String,
    pub confidence: f64,
    pub evidence: Vec<String>,
}

/// A step within a reasoning trace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReasoningStep {
    pub id: String,
    pub step_type: String,
    pub input: String,
    pub output: String,
    pub confidence: f64,
    pub dependencies: Vec<String>,
    pub rationale: Option<String>,
}

/// Header fields for any event bus event.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventHeader {
    pub event_type: String,
    pub version: u64,
    pub source: SovereignUri,
    pub actor: SovereignUri,
    pub timestamp: Timestamp,
    pub trace_id: String,
    pub previous_event: Option<String>,
}

/// A named group of compute nodes sharing a fabric leaf or rail (RFC-0030).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopologyGroup {
    pub id: String,
    pub fabric: String,
    pub nodes: Vec<String>,
    pub leaf: Option<String>,
    pub locality_score: u32,
}

/// A link between two fabric elements (RFC-0030).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricLink {
    pub source: String,
    pub destination: String,
    pub bandwidth_gbps: u64,
    pub latency_us: u64,
}

/// Locality cost between compute nodes for KV placement (RFC-0030).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryLocality {
    pub source_node: String,
    pub target_node: String,
    pub cost: u32,
}

/// Memory tier classification.
///
/// Implements the Memory Hierarchy (Future Layer #26):
/// - Tier 0: Session (seconds–minutes)
/// - Tier 1: Personal (days–weeks)
/// - Tier 2: Organizational (months–years)
/// - Tier 3: Civilizational (decades)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MemoryTier {
    /// Session memory — volatile, seconds to minutes.
    Session,
    /// Personal memory — persisted, days to weeks.
    Personal,
    /// Organizational memory — shared, months to years.
    Organizational,
    /// Civilizational memory — global, decades.
    Civilizational,
}

impl fmt::Display for MemoryTier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Session => write!(f, "session"),
            Self::Personal => write!(f, "personal"),
            Self::Organizational => write!(f, "organizational"),
            Self::Civilizational => write!(f, "civilizational"),
        }
    }
}

/// Jurisdiction information for sovereign compliance.
///
/// Implements Jurisdiction-Aware Federation (Future Layer #15).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Jurisdiction {
    /// Data region (e.g., "EU", "US", "CZ").
    pub region: String,
    /// Applicable regulation (e.g., "GDPR", "CCPA").
    pub regulation: Option<String>,
    /// Data export policy.
    pub allow_export: bool,
    /// Replication policy.
    pub replication_policy: ReplicationPolicy,
}

/// Policy for data replication across nodes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplicationPolicy {
    /// Replicate freely.
    Open,
    /// Only replicate to trusted nodes.
    TrustedOnly,
    /// Never replicate.
    Denied,
}

impl Default for ReplicationPolicy {
    fn default() -> Self {
        Self::TrustedOnly
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::uri::{UriScheme, SovereignUri};

    #[test]
    fn provenance_entry_creation() {
        let agent = SovereignUri::new(UriScheme::Agent, "creator");
        let entry = ProvenanceEntry {
            action: "created".into(),
            agent: agent.clone(),
            timestamp: Timestamp::now(),
            previous: None,
            reason: None,
        };
        assert_eq!(entry.action, "created");
        assert_eq!(entry.agent, agent);
    }

    #[test]
    fn trust_score_clamping() {
        let ts = TrustScore::new(150);
        assert_eq!(ts.value, 100);
        let ts2 = TrustScore::new(75);
        assert!(ts2.meets_threshold(70));
        assert!(!ts2.meets_threshold(80));
    }

    #[test]
    fn capability_descriptor_roundtrip() {
        let provider = SovereignUri::new(UriScheme::Agent, "legal-agent");
        let desc = CapabilityDescriptor {
            id: "capability://legal/review".into(),
            provider: provider.clone(),
            display_name: "Legal Review".into(),
            inputs: vec![CapabilityParam { name: "document".into(), param_type: "artifact".into(), required: true }],
            outputs: vec![CapabilityParam { name: "assessment".into(), param_type: "knowledge".into(), required: true }],
            trust_required: 70,
            tags: vec!["legal".into(), "gdpr".into()],
        };
        let json = serde_json::to_string(&desc).unwrap();
        let restored: CapabilityDescriptor = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.id, desc.id);
        assert_eq!(restored.provider, provider);
    }

    #[test]
    fn event_header_creation() {
        let source = SovereignUri::new(UriScheme::Node, "test-node");
        let actor = SovereignUri::new(UriScheme::Agent, "test-agent");
        let header = EventHeader {
            event_type: "agent.spawned".into(),
            version: 1,
            source: source.clone(),
            actor: actor.clone(),
            timestamp: Timestamp::now(),
            trace_id: "trace-abc".into(),
            previous_event: None,
        };
        assert_eq!(header.event_type, "agent.spawned");
        assert_eq!(header.trace_id, "trace-abc");
    }

    #[test]
    fn knowledge_claim_confidence_range() {
        let claim = KnowledgeClaim {
            statement: "F = ma".into(),
            confidence: 0.99,
            evidence: vec!["evidence://exp-001".into()],
        };
        assert!(claim.confidence > 0.0 && claim.confidence <= 1.0);
    }

    #[test]
    fn reasoning_step_dependencies() {
        let step = ReasoningStep {
            id: "step-003".into(),
            step_type: "deduction".into(),
            input: "premises".into(),
            output: "conclusion".into(),
            confidence: 0.95,
            dependencies: vec!["step-001".into(), "step-002".into()],
            rationale: Some("By modus ponens".into()),
        };
        assert_eq!(step.dependencies.len(), 2);
        assert!(step.rationale.is_some());
    }

    #[test]
    fn object_meta_creation() {
        let uri = SovereignUri::new(UriScheme::Agent, "test-agent");
        let creator = SovereignUri::new(UriScheme::Org, "acme");
        let meta = ObjectMeta::new(uri.clone(), creator);

        assert_eq!(meta.version, 1);
        assert_eq!(meta.uri, uri);
        assert!(meta.description.is_none());
    }

    #[test]
    fn object_meta_versioning() {
        let uri = SovereignUri::new(UriScheme::Agent, "test-agent");
        let creator = SovereignUri::new(UriScheme::Org, "acme");
        let mut meta = ObjectMeta::new(uri, creator);

        assert_eq!(meta.version, 1);
        meta.bump_version();
        assert_eq!(meta.version, 2);
    }

    #[test]
    fn object_id_uniqueness() {
        let id1 = ObjectId::new();
        let id2 = ObjectId::new();
        assert_ne!(id1, id2);
    }

    // ── RFC-0030 topology types ─────────────────────────────────────────

    #[test]
    fn topology_group_creation() {
        let group = TopologyGroup {
            id: "topology://zcube-1/group-a".into(),
            fabric: "fabric://zcube-a".into(),
            nodes: vec!["node://gpu-001".into(), "node://gpu-002".into()],
            leaf: Some("leaf://zcube-a/leaf01".into()),
            locality_score: 0,
        };
        assert_eq!(group.nodes.len(), 2);
        assert!(group.leaf.is_some());
    }

    #[test]
    fn fabric_link_roundtrip() {
        let link = FabricLink {
            source: "leaf://zcube-a/leaf01".into(),
            destination: "spine://zcube-a/spine01".into(),
            bandwidth_gbps: 800,
            latency_us: 2,
        };
        let json = serde_json::to_string(&link).unwrap();
        let restored: FabricLink = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.bandwidth_gbps, 800);
        assert_eq!(restored.latency_us, 2);
    }

    #[test]
    fn memory_locality_cost() {
        let loc = MemoryLocality {
            source_node: "node://gpu-001".into(),
            target_node: "node://gpu-032".into(),
            cost: 5,
        };
        assert!(loc.cost > 0);
    }
}
