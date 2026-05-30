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
    /// Reasoning chain: `reason://decision-42`
    Reason,
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
            Self::Reason => "reason",
            Self::Knowledge => "knowledge",
            Self::Capability => "capability",
            Self::Workflow => "workflow",
            Self::Contract => "contract",
            Self::Robot => "robot",
            Self::Policy => "policy",
            Self::Node => "node",
            Self::Event => "event",
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
            "reason" => Ok(Self::Reason),
            "knowledge" => Ok(Self::Knowledge),
            "capability" => Ok(Self::Capability),
            "workflow" => Ok(Self::Workflow),
            "contract" => Ok(Self::Contract),
            "robot" => Ok(Self::Robot),
            "policy" => Ok(Self::Policy),
            "node" => Ok(Self::Node),
            "event" => Ok(Self::Event),
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
        Self {
            scheme,
            authority: authority.into(),
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
        ];

        for uri_str in uris {
            let uri = SovereignUri::parse(uri_str).unwrap();
            assert_eq!(uri.to_string(), uri_str, "roundtrip failed for {uri_str}");
        }
    }
}
