//! # Financial Compliance
//!
//! Regulatory compliance engine for SovereignStack.
//!
//! Maps SovereignStack operations to regulatory frameworks including
//! ISO 20022, PSD2, MiFID II, Basel III/IV, SOX, and Dodd-Frank.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Regulatory framework identifier.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RegulatoryFramework {
    /// ISO 20022 financial messaging.
    Iso20022,
    /// Payment Services Directive 2 (EU).
    Psd2,
    /// Markets in Financial Instruments Directive II (EU).
    MifidII,
    /// Basel III / IV capital requirements.
    BaselIII,
    /// Sarbanes-Oxley Act (US).
    Sox,
    /// Dodd-Frank Wall Street Reform (US).
    DoddFrank,
    /// General Data Protection Regulation (EU).
    Gdpr,
    /// EU AI Act.
    EuAiAct,
    /// Anti-Money Laundering Directive (EU).
    Amld,
    /// Digital Operational Resilience Act (EU).
    Dora,
    /// Custom framework.
    Custom(String),
}

/// A compliance rule within a framework.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceRule {
    pub id: Uuid,
    pub framework: RegulatoryFramework,
    /// Rule identifier (e.g., "Article 5", "Section 404").
    pub rule_id: String,
    pub title: String,
    pub description: String,
    /// SovereignStack controls that satisfy this rule.
    pub mapped_controls: Vec<String>,
    /// Severity if violated.
    pub severity: ComplianceSeverity,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ComplianceSeverity {
    Info,
    Warning,
    Critical,
    Blocking,
}

/// A compliance check result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceCheck {
    pub id: Uuid,
    pub rule: ComplianceRule,
    /// Entity or transaction being checked.
    pub target_uri: String,
    pub result: ComplianceResult,
    pub details: String,
    pub checked_at: DateTime<Utc>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ComplianceResult {
    Compliant,
    NonCompliant,
    PartiallyCompliant,
    NotApplicable,
    PendingReview,
}

/// A compliance report aggregating multiple checks.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComplianceReport {
    pub id: Uuid,
    pub entity_uri: String,
    pub framework: RegulatoryFramework,
    pub checks: Vec<ComplianceCheck>,
    pub overall_status: ComplianceResult,
    /// Controls coverage percentage.
    pub coverage_percent: f64,
    pub generated_at: DateTime<Utc>,
}

/// Regulatory filing.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegulatoryFiling {
    pub id: Uuid,
    pub framework: RegulatoryFramework,
    pub filing_type: String,
    pub entity_uri: String,
    pub content_hash: String,
    pub filed_at: DateTime<Utc>,
    pub accepted_at: Option<DateTime<Utc>>,
    pub status: FilingStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FilingStatus {
    Draft,
    Submitted,
    Accepted,
    Rejected { reason: String },
    Amended,
}

/// Compliance engine trait.
#[async_trait::async_trait]
pub trait ComplianceEngine: Send + Sync {
    /// Check compliance of an entity or transaction against a framework.
    async fn check(&self, target_uri: &str, framework: RegulatoryFramework) -> Result<Vec<ComplianceCheck>, ComplianceError>;
    /// Generate a compliance report.
    async fn report(&self, entity_uri: &str, framework: RegulatoryFramework) -> Result<ComplianceReport, ComplianceError>;
    /// Get rules for a framework.
    async fn rules(&self, framework: RegulatoryFramework) -> Result<Vec<ComplianceRule>, ComplianceError>;
    /// Submit a regulatory filing.
    async fn file(&self, filing: RegulatoryFiling) -> Result<RegulatoryFiling, ComplianceError>;
}

#[derive(Debug, thiserror::Error)]
pub enum ComplianceError {
    #[error("framework not supported: {0:?}")]
    UnsupportedFramework(RegulatoryFramework),
    #[error("entity not found: {0}")]
    EntityNotFound(String),
    #[error("compliance check failed: {0}")]
    CheckFailed(String),
    #[error("filing error: {0}")]
    FilingError(String),
}
