//! # Derivatives
//!
//! Derivative instruments for SovereignStack.
//!
//! URI scheme: `derivative://<contract-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Derivative instrument type.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DerivativeType {
    /// European or American option.
    Option {
        style: OptionStyle,
        direction: OptionDirection,
        strike: i64,
        premium: i64,
    },
    /// Exchange-traded or OTC future.
    Future {
        contract_size: u64,
        margin_requirement: i64,
    },
    /// Interest rate, currency, or credit default swap.
    Swap {
        swap_type: SwapType,
        notional: i64,
        fixed_rate: Option<f64>,
    },
    /// Forward contract.
    Forward {
        forward_price: i64,
        contract_size: u64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptionStyle {
    European,
    American,
    Asian,
    Bermudan,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptionDirection {
    Call,
    Put,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SwapType {
    InterestRate,
    Currency,
    CreditDefault,
    TotalReturn,
    Commodity,
}

/// A derivative contract.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Derivative {
    pub id: Uuid,
    pub uri: String,
    /// Underlying asset URI (asset://, bond://, etc.).
    pub underlying: String,
    /// Counterparty A.
    pub party_a: String,
    /// Counterparty B.
    pub party_b: String,
    pub derivative_type: DerivativeType,
    pub currency: String,
    pub effective_date: DateTime<Utc>,
    pub maturity_date: DateTime<Utc>,
    pub status: DerivativeStatus,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum DerivativeStatus {
    Pending,
    Active,
    Exercised,
    Expired,
    Terminated,
}

/// Valuation of a derivative position.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DerivativeValuation {
    pub derivative_id: Uuid,
    pub mark_to_market: i64,
    pub currency: String,
    /// Greeks (for options).
    pub delta: Option<f64>,
    pub gamma: Option<f64>,
    pub theta: Option<f64>,
    pub vega: Option<f64>,
    pub rho: Option<f64>,
    pub computed_at: DateTime<Utc>,
}

/// Pricing engine trait.
#[async_trait::async_trait]
pub trait PricingEngine: Send + Sync {
    /// Price a derivative contract.
    async fn price(&self, derivative: &Derivative) -> Result<DerivativeValuation, DerivativeError>;
    /// Compute Greeks for an option.
    async fn greeks(&self, derivative: &Derivative) -> Result<DerivativeValuation, DerivativeError>;
}

#[derive(Debug, thiserror::Error)]
pub enum DerivativeError {
    #[error("derivative not found: {0}")]
    NotFound(Uuid),
    #[error("pricing error: {0}")]
    PricingError(String),
    #[error("underlying not found: {0}")]
    UnderlyingNotFound(String),
    #[error("expired contract")]
    Expired,
}
