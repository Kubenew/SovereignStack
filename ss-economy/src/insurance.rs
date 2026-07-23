//! # Insurance
//!
//! Insurance domain primitives for SovereignStack.
//!
//! URI scheme: `insurance://<policy-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Insurance line of business.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LineOfBusiness {
    Life,
    Health,
    Property,
    Casualty,
    Auto,
    Marine,
    Aviation,
    Cyber,
    Liability,
    Reinsurance,
    Custom(String),
}

/// Insurance policy status.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PolicyStatus {
    Quoted,
    Bound,
    Active,
    Lapsed,
    Cancelled,
    Expired,
    ClaimInProgress,
}

/// An insurance policy.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InsurancePolicy {
    pub id: Uuid,
    pub uri: String,
    /// Policyholder (person://, company://).
    pub holder: String,
    /// Underwriter (company://, bank://).
    pub underwriter: String,
    pub line_of_business: LineOfBusiness,
    pub status: PolicyStatus,
    pub coverage: Vec<Coverage>,
    /// Annual premium in smallest currency unit.
    pub premium: i64,
    pub premium_currency: String,
    pub effective_date: DateTime<Utc>,
    pub expiry_date: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
}

/// A coverage item within a policy.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Coverage {
    pub name: String,
    pub description: String,
    /// Maximum coverage amount.
    pub limit: i64,
    /// Deductible amount.
    pub deductible: i64,
    pub currency: String,
}

/// Claim status.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ClaimStatus {
    Filed,
    UnderReview,
    Approved { amount: i64 },
    Denied { reason: String },
    Paid,
    Appealed,
}

/// An insurance claim.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claim {
    pub id: Uuid,
    pub policy_id: Uuid,
    pub claimant: String,
    pub description: String,
    pub claimed_amount: i64,
    pub currency: String,
    pub status: ClaimStatus,
    /// Supporting evidence (evidence:// URIs).
    pub evidence: Vec<String>,
    pub filed_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Insurance provider trait.
#[async_trait::async_trait]
pub trait InsuranceProvider: Send + Sync {
    /// Quote a new policy.
    async fn quote(&self, holder: &str, line: LineOfBusiness, coverage: Vec<Coverage>) -> Result<InsurancePolicy, InsuranceError>;
    /// Bind a quoted policy.
    async fn bind(&self, policy_id: Uuid) -> Result<InsurancePolicy, InsuranceError>;
    /// File a claim.
    async fn file_claim(&self, policy_id: Uuid, description: String, amount: i64) -> Result<Claim, InsuranceError>;
    /// Review and adjudicate a claim.
    async fn adjudicate(&self, claim_id: Uuid, approved: bool, amount: Option<i64>) -> Result<Claim, InsuranceError>;
}

#[derive(Debug, thiserror::Error)]
pub enum InsuranceError {
    #[error("policy not found: {0}")]
    PolicyNotFound(Uuid),
    #[error("claim not found: {0}")]
    ClaimNotFound(Uuid),
    #[error("underwriting rejected: {0}")]
    UnderwritingRejected(String),
    #[error("coverage exceeded")]
    CoverageExceeded,
}
