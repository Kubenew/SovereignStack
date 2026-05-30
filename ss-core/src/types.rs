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
}
