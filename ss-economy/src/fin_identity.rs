//! # Financial Identity
//!
//! KYC, AML, and sanctions screening for SovereignStack.
//!
//! Named `fin_identity` to avoid collision with the `ss-identity` crate
//! which handles sovereign agent identity.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// KYC verification status.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum KycStatus {
    /// Not yet verified.
    Unverified,
    /// Verification in progress.
    Pending,
    /// Identity verified.
    Verified,
    /// Enhanced due diligence completed.
    EnhancedDueDiligence,
    /// Verification failed.
    Failed { reason: String },
    /// Verification expired (requires renewal).
    Expired,
}

/// KYC risk tier.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum KycRiskTier {
    Low,
    Medium,
    High,
    Prohibited,
}

/// A KYC profile for a digital twin.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KycProfile {
    pub id: Uuid,
    /// Entity being verified (person://, company://).
    pub entity_uri: String,
    pub status: KycStatus,
    pub risk_tier: KycRiskTier,
    /// Verification provider.
    pub provider: String,
    /// Document types verified (passport, utility bill, etc.).
    pub verified_documents: Vec<String>,
    /// Politically Exposed Person flag.
    pub pep_status: bool,
    /// Adverse media screening result.
    pub adverse_media: bool,
    pub verified_at: Option<DateTime<Utc>>,
    pub expires_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

/// AML check result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AmlCheck {
    pub id: Uuid,
    pub entity_uri: String,
    /// Transaction or payment being checked.
    pub transaction_uri: Option<String>,
    pub result: AmlResult,
    /// Suspicious activity indicators.
    pub indicators: Vec<String>,
    /// SAR (Suspicious Activity Report) filed.
    pub sar_filed: bool,
    pub checked_at: DateTime<Utc>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum AmlResult {
    Clear,
    FlaggedForReview,
    Blocked,
}

/// Sanctions screening result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SanctionsCheck {
    pub id: Uuid,
    pub entity_uri: String,
    /// Lists checked (OFAC SDN, EU Sanctions, UN, etc.).
    pub lists_checked: Vec<String>,
    pub matches: Vec<SanctionsMatch>,
    pub result: SanctionsResult,
    pub checked_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SanctionsMatch {
    pub list_name: String,
    pub matched_name: String,
    pub confidence: f64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SanctionsResult {
    Clear,
    PotentialMatch,
    Sanctioned,
}

/// Financial identity provider trait.
#[async_trait::async_trait]
pub trait FinancialIdentityProvider: Send + Sync {
    /// Run KYC verification for an entity.
    async fn verify_kyc(&self, entity_uri: &str) -> Result<KycProfile, FinIdentityError>;
    /// Run AML check on a transaction.
    async fn check_aml(&self, entity_uri: &str, transaction_uri: Option<&str>) -> Result<AmlCheck, FinIdentityError>;
    /// Screen against sanctions lists.
    async fn screen_sanctions(&self, entity_uri: &str) -> Result<SanctionsCheck, FinIdentityError>;
    /// Get current KYC profile.
    async fn get_kyc_profile(&self, entity_uri: &str) -> Result<KycProfile, FinIdentityError>;
}

#[derive(Debug, thiserror::Error)]
pub enum FinIdentityError {
    #[error("entity not found: {0}")]
    EntityNotFound(String),
    #[error("verification provider error: {0}")]
    ProviderError(String),
    #[error("sanctioned entity: {0}")]
    Sanctioned(String),
}
