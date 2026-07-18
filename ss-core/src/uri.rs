//! Sovereign URI — Universal addressing for the intelligence network.
//!
//! Every object in SovereignStack has a globally unique, resolvable URI
//! following the scheme: `scheme://authority/path[?query][#fragment]`

use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

use crate::error::{Error, Result};

/// Registered URI schemes in the SovereignStack network.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UriScheme {
    /// Agent identity: `agent://researcher-1`
    Agent,
    /// Organization: `org://acme`
    Org,
    /// Active session: `session://abc123`
    Session,
    /// Produced artifact: `artifact://sha256:def456`
    Artifact,
    /// Memory object: `memory://xyz789`
    Memory,
    /// Root persistent cognitive state: `mind://enterprise`
    Mind,
    /// Verifiable reasoning graph node: `reason://decision-42`
    Reason,
    /// Active objective: `goal://revenue-q3`
    Goal,
    /// Held proposition: `belief://market-growth`
    Belief,
    /// Knowledge object: `knowledge://physics/newton`
    Knowledge,
    /// Skill/capability: `capability://legal-review`
    Capability,
    /// Workflow definition: `workflow://contract-analysis`
    Workflow,
    /// Agent contract: `contract://task-88`
    Contract,
    /// Physical device: `robot://drone-12`
    Robot,
    /// Governance policy: `policy://gdpr-eu`
    Policy,
    /// Network node: `node://homelab-1`
    Node,
    /// Event record: `event://evt-99`
    Event,
    /// Execution state snapshot: `checkpoint://session-abc/step-42`
    Checkpoint,
    /// Verifiable audit evidence: `evidence://audit-report-2026-q2`
    Evidence,
    /// Cognitive routing entry: `routing://mesh/verifier`
    Routing,
    /// GPU/CPU allocation: `compute://zcube-a/alloc-001`
    Compute,
    /// Network capacity: `bandwidth://zcube-a/stream-042`
    Bandwidth,
    /// Persistent storage: `storage://zcube-a/pool-7`
    Storage,
    /// Power consumption budget: `energy://zcube-a/budget-q3`
    Energy,
    /// Fabric leaf switch: `leaf://fabric-a/leaf03`
    Leaf,
    /// Fabric spine switch: `spine://fabric-a/spine01`
    Spine,
    /// Fabric rail: `rail://fabric-a/rail7`
    Rail,
    /// Named fabric: `fabric://zcube-a`
    Fabric,
    /// Named topology: `topology://cluster-prod`
    Topology,
    /// Named fabric link: `link://zcube-a/link-leaf01-spine01`
    Link,
    /// Telemetry event: `tel://zcube-a/evt-001`
    Tel,
    /// KV cache object: `kv://fabric/gpu-003/session-abc/head-0`
    KV,
    /// Federation gateway: `gateway://eu-frankfurt`
    Gateway,
    /// Memory pool (fabric): `mem://zcube-a/gpu-003/hbm`
    Mem,
    /// Cluster profile: `profile://zcube-standard-v1`
    Profile,
    /// AI model: `model://huggingface/Qwen/Qwen2.5-72B`
    Model,
    /// Dataset: `dataset://huggingface/c4`
    Dataset,
    /// Training run: `training://zcube-a/run-0042`
    Training,
    /// Model evaluation: `evaluation://zcube-a/eval-007`
    Evaluation,
    /// Audit evidence package: `audit-pkg://node-001/2026-06-03`
    AuditPkg,
    /// AI continuity manifest: `continuity://zcube-a/legal-agent`
    Continuity,
    /// Recovery procedure: `recovery://zcube-a/incident-42`
    Recovery,
    /// Failover event: `failover://zcube-a/2026-06-03/evt-001`
    Failover,
    /// Recovery playbook: `playbook://zcube-a/gpu-failure`
    Playbook,
    /// Memory snapshot: `snapshot://zcube-a/gpu-003/snap-001`
    Snapshot,
    /// Agent migration: `migration://zcube-a/gpu-003/agent-42`
    Migration,
    /// Meta-cognition: `meta://agent/self-model`
    Meta,
    /// Safety guard: `safeguard://veto-node-01`
    Safeguard,
    /// Values charter: `values://org/ethics-charter`
    Values,
    /// Protocol version: `protocol://ss-kernel/v2`
    Protocol,
    /// Human operator: `operator://alice`
    Operator,
    /// Cognitive sandbox: `sandbox://isolated-zone-9`
    Sandbox,
    /// Cognitive replay: `replay://session/123`
    Replay,
    /// Evolution lineage: `lineage://agent/improvement-log`
    Lineage,
    /// Cognitive lease: `lease://agent/finance`
    Lease,
    /// Self-model: `self://agent/metacognition`
    Self_,
    /// Reflection log: `reflection://agent/insight-42`
    Reflection,
    /// Improvement record: `improvement://agent/patch-v3`
    Improvement,
    /// Explanation trace: `explanation://reason/step-7`
    Explanation,
    /// Summary artifact: `summary://session/digest`
    Summary,
    /// Timeline index: `timeline://agent/history`
    Timeline,
    /// Governance decision: `governance://org/proposal-88`
    Governance,
    /// Digital twin: `twin://agent/candidate`
    Twin,
    /// Unified identity: `identity://human/alice`
    Identity,
    /// Federation mesh: `mesh://eu-fabric`
    Mesh,
    /// World model: `world://sim/environment`
    World,
    /// Execution plan: `plan://agent/strategy-7`
    Plan,
    /// Tool binding: `tool://agent/calculator`
    Tool,
    /// Identity transition certificate: `transition://agent/from-version/to-version`
    Transition,
    /// Raw idea: `idea://project/1234`
    Idea,
    /// Research artifact: `research://topic/source`
    Research,
    /// Architectural decision record: `decision://project/ADR-042`
    Decision,
    /// Architecture boundary: `architecture://module/name`
    Architecture,
    /// Feature specification: `spec://feature/name`
    Spec,
    /// Build plan: `build://project/epic`
    Build,
    /// Release artifact: `release://project/version`
    Release,
    /// Project state: `project://id`
    Project,
    /// Workflow routing: `flow://router/route`
    Flow,
}

impl UriScheme {
    /// Returns the string representation of the scheme.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Agent => "agent",
            Self::Org => "org",
            Self::Session => "session",
            Self::Artifact => "artifact",
            Self::Memory => "memory",
            Self::Mind => "mind",
            Self::Reason => "reason",
            Self::Goal => "goal",
            Self::Belief => "belief",
            Self::Knowledge => "knowledge",
            Self::Capability => "capability",
            Self::Workflow => "workflow",
            Self::Contract => "contract",
            Self::Robot => "robot",
            Self::Policy => "policy",
            Self::Node => "node",
            Self::Event => "event",
            Self::Checkpoint => "checkpoint",
            Self::Evidence => "evidence",
            Self::Routing => "routing",
            Self::Compute => "compute",
            Self::Bandwidth => "bandwidth",
            Self::Storage => "storage",
            Self::Energy => "energy",
            Self::Leaf => "leaf",
            Self::Spine => "spine",
            Self::Rail => "rail",
            Self::Fabric => "fabric",
            Self::Topology => "topology",
            Self::Link => "link",
            Self::Tel => "tel",
            Self::KV => "kv",
            Self::Gateway => "gateway",
            Self::Mem => "mem",
            Self::Profile => "profile",
            Self::Model => "model",
            Self::Dataset => "dataset",
            Self::Training => "training",
            Self::Evaluation => "evaluation",
            Self::AuditPkg => "audit-pkg",
            Self::Continuity => "continuity",
            Self::Recovery => "recovery",
            Self::Failover => "failover",
            Self::Playbook => "playbook",
            Self::Snapshot => "snapshot",
            Self::Migration => "migration",
            Self::Meta => "meta",
            Self::Safeguard => "safeguard",
            Self::Values => "values",
            Self::Protocol => "protocol",
            Self::Operator => "operator",
            Self::Sandbox => "sandbox",
            Self::Replay => "replay",
            Self::Lineage => "lineage",
            Self::Lease => "lease",
            Self::Self_ => "self",
            Self::Reflection => "reflection",
            Self::Improvement => "improvement",
            Self::Explanation => "explanation",
            Self::Summary => "summary",
            Self::Timeline => "timeline",
            Self::Governance => "governance",
            Self::Twin => "twin",
            Self::Identity => "identity",
            Self::Mesh => "mesh",
            Self::World => "world",
            Self::Plan => "plan",
            Self::Tool => "tool",
            Self::Transition => "transition",
            Self::Idea => "idea",
            Self::Research => "research",
            Self::Decision => "decision",
            Self::Architecture => "architecture",
            Self::Spec => "spec",
            Self::Build => "build",
            Self::Release => "release",
            Self::Project => "project",
            Self::Flow => "flow",
        }
    }
}

impl FromStr for UriScheme {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        match s {
            "agent" => Ok(Self::Agent),
            "org" => Ok(Self::Org),
            "session" => Ok(Self::Session),
            "artifact" => Ok(Self::Artifact),
            "memory" => Ok(Self::Memory),
            "mind" => Ok(Self::Mind),
            "reason" => Ok(Self::Reason),
            "goal" => Ok(Self::Goal),
            "belief" => Ok(Self::Belief),
            "knowledge" => Ok(Self::Knowledge),
            "capability" => Ok(Self::Capability),
            "workflow" => Ok(Self::Workflow),
            "contract" => Ok(Self::Contract),
            "robot" => Ok(Self::Robot),
            "policy" => Ok(Self::Policy),
            "node" => Ok(Self::Node),
            "event" => Ok(Self::Event),
            "checkpoint" => Ok(Self::Checkpoint),
            "evidence" => Ok(Self::Evidence),
            "routing" => Ok(Self::Routing),
            "compute" => Ok(Self::Compute),
            "bandwidth" => Ok(Self::Bandwidth),
            "storage" => Ok(Self::Storage),
            "energy" => Ok(Self::Energy),
            "leaf" => Ok(Self::Leaf),
            "spine" => Ok(Self::Spine),
            "rail" => Ok(Self::Rail),
            "fabric" => Ok(Self::Fabric),
            "topology" => Ok(Self::Topology),
            "link" => Ok(Self::Link),
            "tel" => Ok(Self::Tel),
            "kv" => Ok(Self::KV),
            "gateway" => Ok(Self::Gateway),
            "mem" => Ok(Self::Mem),
            "profile" => Ok(Self::Profile),
            "model" => Ok(Self::Model),
            "dataset" => Ok(Self::Dataset),
            "training" => Ok(Self::Training),
            "evaluation" => Ok(Self::Evaluation),
            "audit-pkg" => Ok(Self::AuditPkg),
            "continuity" => Ok(Self::Continuity),
            "recovery" => Ok(Self::Recovery),
            "failover" => Ok(Self::Failover),
            "playbook" => Ok(Self::Playbook),
            "snapshot" => Ok(Self::Snapshot),
            "migration" => Ok(Self::Migration),
            "meta" => Ok(Self::Meta),
            "safeguard" => Ok(Self::Safeguard),
            "values" => Ok(Self::Values),
            "protocol" => Ok(Self::Protocol),
            "operator" => Ok(Self::Operator),
            "human" => Ok(Self::Operator),
            "sandbox" => Ok(Self::Sandbox),
            "replay" => Ok(Self::Replay),
            "lineage" => Ok(Self::Lineage),
            "lease" => Ok(Self::Lease),
            "self" => Ok(Self::Self_),
            "reflection" => Ok(Self::Reflection),
            "improvement" => Ok(Self::Improvement),
            "explanation" => Ok(Self::Explanation),
            "summary" => Ok(Self::Summary),
            "timeline" => Ok(Self::Timeline),
            "governance" => Ok(Self::Governance),
            "twin" => Ok(Self::Twin),
            "identity" => Ok(Self::Identity),
            "mesh" => Ok(Self::Mesh),
            "world" => Ok(Self::World),
            "plan" => Ok(Self::Plan),
            "tool" => Ok(Self::Tool),
            "transition" => Ok(Self::Transition),
            "idea" => Ok(Self::Idea),
            "research" => Ok(Self::Research),
            "decision" => Ok(Self::Decision),
            "architecture" => Ok(Self::Architecture),
            "spec" => Ok(Self::Spec),
            "build" => Ok(Self::Build),
            "release" => Ok(Self::Release),
            "project" => Ok(Self::Project),
            "flow" => Ok(Self::Flow),
            _ => Err(Error::InvalidUri(format!("unknown scheme: {s}"))),
        }
    }
}

impl fmt::Display for UriScheme {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// A Sovereign URI — the universal address for any object in SovereignStack.
///
/// Format: `scheme://authority/path[?query][#fragment]`
///
/// # Examples
///
/// ```rust
/// use ss_core::SovereignUri;
///
/// let uri = SovereignUri::parse("agent://researcher-1").unwrap();
/// assert_eq!(uri.scheme().as_str(), "agent");
/// assert_eq!(uri.authority(), "researcher-1");
///
/// let uri = SovereignUri::parse("knowledge://physics/newton/v2").unwrap();
/// assert_eq!(uri.scheme().as_str(), "knowledge");
/// assert_eq!(uri.authority(), "physics");
/// assert_eq!(uri.path(), Some("newton/v2"));
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SovereignUri {
    scheme: UriScheme,
    authority: String,
    path: Option<String>,
    query: Option<String>,
    fragment: Option<String>,
}

impl SovereignUri {
    /// Parse a string into a SovereignUri.
    pub fn parse(input: &str) -> Result<Self> {
        // Split scheme from rest
        let (scheme_str, rest) = input
            .split_once("://")
            .ok_or_else(|| Error::InvalidUri(format!("missing '://' in URI: {input}")))?;

        let scheme = UriScheme::from_str(scheme_str)?;

        // Split fragment
        let (rest, fragment) = match rest.split_once('#') {
            Some((r, f)) => (r, Some(f.to_string())),
            None => (rest, None),
        };

        // Split query
        let (rest, query) = match rest.split_once('?') {
            Some((r, q)) => (r, Some(q.to_string())),
            None => (rest, None),
        };

        // Split authority from path
        let (authority, path) = match rest.split_once('/') {
            Some((a, p)) if !p.is_empty() => (a.to_string(), Some(p.to_string())),
            _ => (rest.to_string(), None),
        };

        if authority.is_empty() {
            return Err(Error::InvalidUri(format!("empty authority in URI: {input}")));
        }

        Ok(Self {
            scheme,
            authority,
            path,
            query,
            fragment,
        })
    }

    /// Create a new SovereignUri from components.
    pub fn new(scheme: UriScheme, authority: impl Into<String>) -> Self {
        let auth = authority.into();
        assert!(!auth.is_empty(), "authority cannot be empty");
        Self {
            scheme,
            authority: auth,
            path: None,
            query: None,
            fragment: None,
        }
    }

    /// Add a path to this URI.
    pub fn with_path(mut self, path: impl Into<String>) -> Self {
        self.path = Some(path.into());
        self
    }

    /// Add a query string to this URI.
    pub fn with_query(mut self, query: impl Into<String>) -> Self {
        self.query = Some(query.into());
        self
    }

    /// Add a fragment to this URI.
    pub fn with_fragment(mut self, fragment: impl Into<String>) -> Self {
        self.fragment = Some(fragment.into());
        self
    }

    /// Returns the URI scheme.
    pub fn scheme(&self) -> UriScheme {
        self.scheme
    }

    /// Returns the authority component.
    pub fn authority(&self) -> &str {
        &self.authority
    }

    /// Returns the path component, if any.
    pub fn path(&self) -> Option<&str> {
        self.path.as_deref()
    }

    /// Returns the query component, if any.
    pub fn query(&self) -> Option<&str> {
        self.query.as_deref()
    }

    /// Returns the fragment component, if any.
    pub fn fragment(&self) -> Option<&str> {
        self.fragment.as_deref()
    }

    /// Returns true if this URI refers to an agent.
    pub fn is_agent(&self) -> bool {
        self.scheme == UriScheme::Agent
    }

    /// Returns true if this URI refers to a knowledge object.
    pub fn is_knowledge(&self) -> bool {
        self.scheme == UriScheme::Knowledge
    }

    /// Returns true if this URI refers to a capability.
    pub fn is_capability(&self) -> bool {
        self.scheme == UriScheme::Capability
    }
}

impl fmt::Display for SovereignUri {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}://{}", self.scheme, self.authority)?;
        if let Some(ref path) = self.path {
            write!(f, "/{path}")?;
        }
        if let Some(ref query) = self.query {
            write!(f, "?{query}")?;
        }
        if let Some(ref fragment) = self.fragment {
            write!(f, "#{fragment}")?;
        }
        Ok(())
    }
}

impl FromStr for SovereignUri {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        Self::parse(s)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_simple_agent_uri() {
        let uri = SovereignUri::parse("agent://researcher-1").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Agent);
        assert_eq!(uri.authority(), "researcher-1");
        assert_eq!(uri.path(), None);
        assert!(uri.is_agent());
    }

    #[test]
    fn parse_knowledge_uri_with_path() {
        let uri = SovereignUri::parse("knowledge://physics/newton/v2").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Knowledge);
        assert_eq!(uri.authority(), "physics");
        assert_eq!(uri.path(), Some("newton/v2"));
        assert!(uri.is_knowledge());
    }

    #[test]
    fn parse_capability_uri() {
        let uri = SovereignUri::parse("capability://legal-review").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Capability);
        assert_eq!(uri.authority(), "legal-review");
        assert!(uri.is_capability());
    }

    #[test]
    fn parse_uri_with_query_and_fragment() {
        let uri = SovereignUri::parse("agent://alice?version=2#latest").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Agent);
        assert_eq!(uri.authority(), "alice");
        assert_eq!(uri.query(), Some("version=2"));
        assert_eq!(uri.fragment(), Some("latest"));
    }

    #[test]
    fn uri_roundtrip() {
        let original = "knowledge://physics/newton/v2";
        let uri = SovereignUri::parse(original).unwrap();
        assert_eq!(uri.to_string(), original);
    }

    #[test]
    fn uri_builder() {
        let uri = SovereignUri::new(UriScheme::Agent, "researcher-1")
            .with_path("tasks")
            .with_query("status=active");
        assert_eq!(uri.to_string(), "agent://researcher-1/tasks?status=active");
    }

    #[test]
    fn reject_invalid_scheme() {
        assert!(SovereignUri::parse("ftp://example.com").is_err());
    }

    #[test]
    fn reject_missing_authority() {
        assert!(SovereignUri::parse("agent://").is_err());
    }

    #[test]
    fn reject_missing_separator() {
        assert!(SovereignUri::parse("agent:researcher").is_err());
    }

    #[test]
    fn all_schemes_roundtrip() {
        let uris = vec![
            "agent://test",
            "org://acme",
            "session://abc123",
            "artifact://sha256-def",
            "memory://xyz789",
            "reason://decision-42",
            "knowledge://physics",
            "capability://legal-review",
            "workflow://contract-analysis",
            "contract://task-88",
            "robot://drone-12",
            "policy://gdpr-eu",
            "node://homelab-1",
            "event://evt-99",
            "checkpoint://session-abc/step-42",
            "evidence://audit-report-2026-q2",
            "routing://mesh/verifier",
            "compute://zcube-a/alloc-001",
            "bandwidth://zcube-a/stream-042",
            "storage://zcube-a/pool-7",
            "energy://zcube-a/budget-q3",
            "leaf://fabric-a/leaf03",
            "spine://fabric-a/spine01",
            "rail://fabric-a/rail7",
            "fabric://zcube-a",
            "topology://cluster-prod",
            "link://zcube-a/link-leaf01-spine01",
            "tel://zcube-a/evt-001",
            "kv://zcube-a/gpu-003/session-abc/head-0",
            "gateway://eu-frankfurt",
            "mem://zcube-a/gpu-003/hbm",
            "profile://zcube-standard-v1",
            "model://huggingface/Qwen/Qwen2.5-72B",
            "dataset://huggingface/c4",
            "training://zcube-a/run-0042",
            "evaluation://zcube-a/eval-007",
            "audit-pkg://node-001/2026-06-03",
            "continuity://zcube-a/legal-agent",
            "recovery://zcube-a/incident-42",
            "failover://zcube-a/2026-06-03/evt-001",
            "playbook://zcube-a/gpu-failure",
        ];

        for uri_str in uris {
            let uri = SovereignUri::parse(uri_str).unwrap();
            assert_eq!(uri.to_string(), uri_str, "roundtrip failed for {uri_str}");
        }
    }

    #[test]
    fn parse_leaf_uri() {
        let uri = SovereignUri::parse("leaf://fabric-a/leaf03").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Leaf);
        assert_eq!(uri.authority(), "fabric-a");
        assert_eq!(uri.path(), Some("leaf03"));
    }

    #[test]
    fn parse_fabric_uri() {
        let uri = SovereignUri::parse("fabric://zcube-a").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Fabric);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), None);
    }

    #[test]
    fn parse_rail_uri() {
        let uri = SovereignUri::parse("rail://fabric-a/rail7").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Rail);
        assert_eq!(uri.authority(), "fabric-a");
        assert_eq!(uri.path(), Some("rail7"));
    }

    #[test]
    fn parse_topology_uri() {
        let uri = SovereignUri::parse("topology://cluster-prod").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Topology);
        assert_eq!(uri.authority(), "cluster-prod");
    }

    #[test]
    fn parse_tel_uri() {
        let uri = SovereignUri::parse("tel://zcube-a/evt-001").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Tel);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("evt-001"));
    }

    #[test]
    fn parse_kv_uri() {
        let uri = SovereignUri::parse("kv://zcube-a/gpu-003/session-abc/head-0").unwrap();
        assert_eq!(uri.scheme(), UriScheme::KV);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("gpu-003/session-abc/head-0"));
    }

    #[test]
    fn parse_gateway_uri() {
        let uri = SovereignUri::parse("gateway://eu-frankfurt").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Gateway);
        assert_eq!(uri.authority(), "eu-frankfurt");
    }

    #[test]
    fn parse_mem_uri() {
        let uri = SovereignUri::parse("mem://zcube-a/gpu-003/hbm").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Mem);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("gpu-003/hbm"));
    }

    #[test]
    fn parse_profile_uri() {
        let uri = SovereignUri::parse("profile://zcube-standard-v1").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Profile);
        assert_eq!(uri.authority(), "zcube-standard-v1");
    }

    #[test]
    fn parse_model_uri() {
        let uri = SovereignUri::parse("model://huggingface/Qwen/Qwen2.5-72B").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Model);
        assert_eq!(uri.authority(), "huggingface");
        assert_eq!(uri.path(), Some("Qwen/Qwen2.5-72B"));
    }

    #[test]
    fn parse_dataset_uri() {
        let uri = SovereignUri::parse("dataset://huggingface/c4").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Dataset);
        assert_eq!(uri.authority(), "huggingface");
        assert_eq!(uri.path(), Some("c4"));
    }

    #[test]
    fn parse_training_uri() {
        let uri = SovereignUri::parse("training://zcube-a/run-0042").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Training);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("run-0042"));
    }

    #[test]
    fn parse_evaluation_uri() {
        let uri = SovereignUri::parse("evaluation://zcube-a/eval-007").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Evaluation);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("eval-007"));
    }

    #[test]
    fn parse_audit_pkg_uri() {
        let uri = SovereignUri::parse("audit-pkg://node-001/2026-06-03").unwrap();
        assert_eq!(uri.scheme(), UriScheme::AuditPkg);
        assert_eq!(uri.authority(), "node-001");
        assert_eq!(uri.path(), Some("2026-06-03"));
    }

    #[test]
    fn parse_continuity_uri() {
        let uri = SovereignUri::parse("continuity://zcube-a/legal-agent").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Continuity);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("legal-agent"));
    }

    #[test]
    fn parse_recovery_uri() {
        let uri = SovereignUri::parse("recovery://zcube-a/incident-42").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Recovery);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("incident-42"));
    }

    #[test]
    fn parse_failover_uri() {
        let uri = SovereignUri::parse("failover://zcube-a/2026-06-03/evt-001").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Failover);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("2026-06-03/evt-001"));
    }

    #[test]
    fn parse_playbook_uri() {
        let uri = SovereignUri::parse("playbook://zcube-a/gpu-failure").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Playbook);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("gpu-failure"));
    }

    #[test]
    fn parse_checkpoint_uri() {
        let uri = SovereignUri::parse("checkpoint://cluster-a/agent-42/state-7").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Checkpoint);
        assert_eq!(uri.authority(), "cluster-a");
        assert_eq!(uri.path(), Some("agent-42/state-7"));
    }

    #[test]
    fn parse_snapshot_uri() {
        let uri = SovereignUri::parse("snapshot://zcube-a/gpu-003/snap-001").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Snapshot);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("gpu-003/snap-001"));
    }

    #[test]
    fn parse_migration_uri() {
        let uri = SovereignUri::parse("migration://zcube-a/gpu-003/agent-42").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Migration);
        assert_eq!(uri.authority(), "zcube-a");
        assert_eq!(uri.path(), Some("gpu-003/agent-42"));
    }

    #[test]
    fn parse_meta_uri() {
        let uri = SovereignUri::parse("meta://agent/self-model").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Meta);
    }

    #[test]
    fn parse_self_uri() {
        let uri = SovereignUri::parse("self://agent/metacognition").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Self_);
    }

    #[test]
    fn parse_governance_uri() {
        let uri = SovereignUri::parse("governance://org/proposal-88").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Governance);
    }

    #[test]
    fn parse_twin_uri() {
        let uri = SovereignUri::parse("twin://agent/candidate").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Twin);
    }

    #[test]
    fn parse_identity_uri() {
        let uri = SovereignUri::parse("identity://human/alice").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Identity);
    }

    #[test]
    fn parse_mesh_uri() {
        let uri = SovereignUri::parse("mesh://eu-fabric").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Mesh);
    }

    #[test]
    fn parse_world_uri() {
        let uri = SovereignUri::parse("world://sim/environment").unwrap();
        assert_eq!(uri.scheme(), UriScheme::World);
    }

    #[test]
    fn parse_plan_uri() {
        let uri = SovereignUri::parse("plan://agent/strategy-7").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Plan);
    }

    #[test]
    fn parse_tool_uri() {
        let uri = SovereignUri::parse("tool://agent/calculator").unwrap();
        assert_eq!(uri.scheme(), UriScheme::Tool);
    }

    #[test]
    fn parse_all_roundtrip() {
        let schemes = [
            ("self", UriScheme::Self_),
            ("reflection", UriScheme::Reflection),
            ("improvement", UriScheme::Improvement),
            ("explanation", UriScheme::Explanation),
            ("summary", UriScheme::Summary),
            ("timeline", UriScheme::Timeline),
            ("governance", UriScheme::Governance),
            ("twin", UriScheme::Twin),
            ("identity", UriScheme::Identity),
            ("mesh", UriScheme::Mesh),
            ("world", UriScheme::World),
            ("plan", UriScheme::Plan),
            ("tool", UriScheme::Tool),
            ("transition", UriScheme::Transition),
            ("idea", UriScheme::Idea),
            ("research", UriScheme::Research),
            ("decision", UriScheme::Decision),
            ("architecture", UriScheme::Architecture),
            ("spec", UriScheme::Spec),
            ("build", UriScheme::Build),
            ("release", UriScheme::Release),
            ("project", UriScheme::Project),
            ("flow", UriScheme::Flow),
        ];
        for (s, expected) in &schemes {
            let parsed: UriScheme = s.parse().unwrap();
            assert_eq!(&parsed, expected, "scheme: {s}");
            assert_eq!(parsed.as_str(), *s);
        }
    }
}
