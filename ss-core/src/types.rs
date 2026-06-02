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

/// A measured latency distribution (RFC-0032).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatencyStats {
    pub min: f64,
    pub avg: f64,
    pub max: f64,
    pub p99: f64,
}

/// A measured bandwidth distribution (RFC-0032).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BandwidthStats {
    pub min: u64,
    pub avg: u64,
    pub max: u64,
    pub p99: u64,
}

/// A single hop in a computed fabric route (RFC-0032).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricHop {
    pub node: String,
    pub egress_link: Option<String>,
}

/// A computed fabric route between source and target (RFC-0032).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricRoute {
    pub source: String,
    pub target: String,
    pub hops: Vec<FabricHop>,
    pub estimated_latency_us: u64,
    pub available_bandwidth_gbps: u64,
}

/// A reservation of a fabric segment (RFC-0032).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricReservation {
    pub id: String,
    pub fabric: String,
    pub collective: Option<String>,
    pub participants: Vec<String>,
    pub allocated_bandwidth_gbps: u64,
    pub expires_at: String,
    pub lease_token: String,
}

/// A one-shot fabric measurement result (RFC-0032).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricMeasurement {
    pub source: String,
    pub target: String,
    pub latency_us: LatencyStats,
    pub bandwidth_gbps: BandwidthStats,
    pub measured_at: String,
}

/// A KV cache placement known to the scheduler (RFC-0031).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVCachePlacement {
    pub cache_id: String,
    pub node_id: String,
    pub session_id: String,
    pub model: String,
    pub layer: u32,
    pub context_length: u32,
    pub size_mb: u64,
    pub created_at: Timestamp,
}

/// Composite locality score between two nodes (RFC-0031).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalityScore {
    pub source_node: String,
    pub target_node: String,
    pub topology_distance: f64,
    pub kv_transfer_cost: f64,
    pub network_cost: f64,
    pub composite_score: f64,
}

/// A single schedule ranking for a candidate node (RFC-0031).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleRank {
    pub node_id: String,
    pub gpu_score: f64,
    pub capability_score: f64,
    pub trust_score: f64,
    pub network_cost: f64,
    pub kv_transfer_cost: f64,
    pub composite_score: f64,
}

/// Scheduler configuration with tunable weights (RFC-0031).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulerConfig {
    pub gpu_capacity_weight: f64,
    pub capability_weight: f64,
    pub trust_weight: f64,
    pub network_weight: f64,
    pub kv_locality_weight: f64,
    pub prefill_decode_colocation: bool,
    pub kv_transfer_budget_ms: u64,
}

impl Default for SchedulerConfig {
    fn default() -> Self {
        Self {
            gpu_capacity_weight: 0.15,
            capability_weight: 0.15,
            trust_weight: 0.20,
            network_weight: 0.15,
            kv_locality_weight: 0.35,
            prefill_decode_colocation: true,
            kv_transfer_budget_ms: 20,
        }
    }
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

    // ── RFC-0032 fabric protocol types ────────────────────────────────────

    #[test]
    fn latencystats_ordering() {
        let s = LatencyStats { min: 1.0, avg: 2.5, max: 10.0, p99: 8.0 };
        assert!(s.min <= s.avg);
        assert!(s.avg <= s.max);
        assert!(s.p99 <= s.max);
    }

    #[test]
    fn bandwidthstats_roundtrip() {
        let s = BandwidthStats { min: 400, avg: 750, max: 800, p99: 790 };
        let json = serde_json::to_string(&s).unwrap();
        let restored: BandwidthStats = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.max, 800);
    }

    #[test]
    fn fabric_route_creation() {
        let route = FabricRoute {
            source: "node://gpu-001".into(),
            target: "node://gpu-064".into(),
            hops: vec![
                FabricHop { node: "node://gpu-001".into(), egress_link: Some("link://zcube-a/link-gpu001-leaf01".into()) },
                FabricHop { node: "leaf://zcube-a/leaf01".into(), egress_link: Some("link://zcube-a/link-leaf01-spine03".into()) },
                FabricHop { node: "spine://zcube-a/spine03".into(), egress_link: None },
                FabricHop { node: "node://gpu-064".into(), egress_link: None },
            ],
            estimated_latency_us: 7,
            available_bandwidth_gbps: 400,
        };
        assert_eq!(route.hops.len(), 4);
        assert_eq!(route.estimated_latency_us, 7);
    }

    #[test]
    fn fabric_reservation_lease_token() {
        let res = FabricReservation {
            id: "r-001".into(),
            fabric: "fabric://zcube-a".into(),
            collective: Some("all_reduce".into()),
            participants: vec!["node://gpu-001".into(), "node://gpu-002".into()],
            allocated_bandwidth_gbps: 400,
            expires_at: "2026-06-02T12:05:00Z".into(),
            lease_token: "token:ed25519:base64...".into(),
        };
        assert!(res.lease_token.starts_with("token:"));
    }

    #[test]
    fn fabric_measurement_stats() {
        let m = FabricMeasurement {
            source: "link://zcube-a/link-gpu001-leaf01".into(),
            target: "link://zcube-a/link-gpu064-leaf02".into(),
            latency_us: LatencyStats { min: 2.1, avg: 2.4, max: 3.8, p99: 3.2 },
            bandwidth_gbps: BandwidthStats { min: 760, avg: 785, max: 800, p99: 795 },
            measured_at: "2026-06-02T12:00:05Z".into(),
        };
        assert!(m.bandwidth_gbps.avg > 0);
        assert!(m.latency_us.avg > 0.0);
    }

    // ── RFC-0031 KV locality scheduling types ──────────────────────────────

    #[test]
    fn kv_cache_placement_creation() {
        let p = KVCachePlacement {
            cache_id: "kv://zcube-a/gpu-003/session-abc/head-0".into(),
            node_id: "node://gpu-003".into(),
            session_id: "session://abc".into(),
            model: "qwen2.5-72b".into(),
            layer: 0,
            context_length: 65536,
            size_mb: 512,
            created_at: Timestamp::now(),
        };
        assert_eq!(p.size_mb, 512);
        assert_eq!(p.context_length, 65536);
    }

    #[test]
    fn locality_score_composite() {
        let s = LocalityScore {
            source_node: "node://gpu-001".into(),
            target_node: "node://gpu-015".into(),
            topology_distance: 0.12,
            kv_transfer_cost: 0.08,
            network_cost: 0.05,
            composite_score: 0.75,
        };
        assert!(s.composite_score > 0.0);
    }

    #[test]
    fn schedule_rank_ordering() {
        let ranks = vec![
            ScheduleRank { node_id: "gpu-015".into(), gpu_score: 0.9, capability_score: 0.8, trust_score: 0.9, network_cost: 0.1, kv_transfer_cost: 0.05, composite_score: 0.85 },
            ScheduleRank { node_id: "gpu-032".into(), gpu_score: 0.7, capability_score: 0.6, trust_score: 0.7, network_cost: 0.3, kv_transfer_cost: 0.25, composite_score: 0.55 },
        ];
        assert!(ranks[0].composite_score > ranks[1].composite_score);
    }

    #[test]
    fn scheduler_config_defaults() {
        let cfg = SchedulerConfig::default();
        assert_eq!(cfg.kv_locality_weight, 0.35);
        assert!(cfg.prefill_decode_colocation);
        assert_eq!(cfg.kv_transfer_budget_ms, 20);
    }
}
