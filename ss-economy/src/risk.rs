//! # Risk
//!
//! Risk assessment and modeling for SovereignStack.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Risk category.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RiskCategory {
    Market,
    Credit,
    Operational,
    Liquidity,
    Counterparty,
    Regulatory,
    Cyber,
    Reputational,
    Model,
    Custom(String),
}

/// Risk factor (an input to risk models).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskFactor {
    pub name: String,
    pub category: RiskCategory,
    pub value: f64,
    pub unit: String,
    pub source: String,
    pub observed_at: DateTime<Utc>,
}

/// A risk score.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskScore {
    pub id: Uuid,
    /// Entity being assessed (person://, company://, portfolio://).
    pub entity_uri: String,
    pub category: RiskCategory,
    /// Score from 0.0 (no risk) to 1.0 (maximum risk).
    pub score: f64,
    /// Confidence in the score (0.0–1.0).
    pub confidence: f64,
    pub model_name: String,
    pub computed_at: DateTime<Utc>,
}

/// Exposure measurement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Exposure {
    pub entity_uri: String,
    pub counterparty_uri: String,
    /// Gross exposure amount.
    pub gross: i64,
    /// Net exposure after netting/collateral.
    pub net: i64,
    pub currency: String,
    pub as_of: DateTime<Utc>,
}

/// Value at Risk (VaR) result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValueAtRisk {
    pub entity_uri: String,
    /// Confidence level (e.g., 0.95 for 95%).
    pub confidence_level: f64,
    /// Time horizon in days.
    pub horizon_days: u32,
    /// VaR amount.
    pub var_amount: i64,
    pub currency: String,
    /// Method used (Historical, Parametric, MonteCarlo).
    pub method: VarMethod,
    pub computed_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum VarMethod {
    Historical,
    Parametric,
    MonteCarlo { simulations: u32 },
}

/// Stress test scenario.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StressScenario {
    pub name: String,
    pub description: String,
    pub factor_shocks: Vec<FactorShock>,
}

/// A shock to a risk factor.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FactorShock {
    pub factor_name: String,
    /// Absolute or relative shock value.
    pub shock_value: f64,
    pub shock_type: ShockType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ShockType {
    Absolute,
    Relative,
}

/// Stress test result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StressTestResult {
    pub scenario: String,
    pub entity_uri: String,
    pub impact_amount: i64,
    pub currency: String,
    pub computed_at: DateTime<Utc>,
}

/// Risk engine trait.
#[async_trait::async_trait]
pub trait RiskEngine: Send + Sync {
    /// Compute a risk score for an entity.
    async fn score(&self, entity_uri: &str, category: RiskCategory) -> Result<RiskScore, RiskError>;
    /// Compute Value at Risk.
    async fn var(&self, entity_uri: &str, confidence: f64, horizon_days: u32) -> Result<ValueAtRisk, RiskError>;
    /// Get exposure to a counterparty.
    async fn exposure(&self, entity_uri: &str, counterparty_uri: &str) -> Result<Exposure, RiskError>;
    /// Run a stress test.
    async fn stress_test(&self, entity_uri: &str, scenario: StressScenario) -> Result<StressTestResult, RiskError>;
}

#[derive(Debug, thiserror::Error)]
pub enum RiskError {
    #[error("entity not found: {0}")]
    EntityNotFound(String),
    #[error("model error: {0}")]
    ModelError(String),
    #[error("insufficient data: {0}")]
    InsufficientData(String),
}
