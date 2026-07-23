//! # Tax
//!
//! Tax computation and jurisdiction handling for SovereignStack.
//!
//! URI scheme: `tax://<jurisdiction>/<event-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Tax type.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaxType {
    /// Value Added Tax / Goods and Services Tax.
    Vat { rate: f64 },
    /// Capital gains tax.
    CapitalGains { short_term_rate: f64, long_term_rate: f64 },
    /// Income tax.
    Income { bracket: String, rate: f64 },
    /// Withholding tax on cross-border payments.
    Withholding { rate: f64, treaty_rate: Option<f64> },
    /// Transaction tax (e.g., FTT, stamp duty).
    Transaction { rate: f64 },
    /// Corporate tax.
    Corporate { rate: f64 },
    /// Custom tax type.
    Custom { name: String, rate: f64 },
}

/// A tax jurisdiction.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaxJurisdiction {
    pub id: Uuid,
    /// ISO 3166-1 country code.
    pub country_code: String,
    /// Sub-jurisdiction (state, province).
    pub subdivision: Option<String>,
    pub name: String,
    /// Applicable tax types.
    pub tax_types: Vec<TaxType>,
    /// Tax treaty partners.
    pub treaty_partners: Vec<String>,
}

/// A taxable event.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaxableEvent {
    pub id: Uuid,
    pub uri: String,
    /// Entity subject to tax.
    pub entity_uri: String,
    /// Source transaction (payment://, trade, etc.).
    pub source_uri: String,
    pub jurisdiction: String,
    pub event_type: TaxableEventType,
    /// Gross amount.
    pub gross_amount: i64,
    /// Tax amount.
    pub tax_amount: i64,
    /// Net amount.
    pub net_amount: i64,
    pub currency: String,
    pub occurred_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaxableEventType {
    Sale,
    Purchase,
    Dividend,
    Interest,
    RoyaltyPayment,
    CapitalGain,
    Employment,
    ServiceFee,
    Custom(String),
}

/// Tax calculation result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaxCalculation {
    pub event_id: Uuid,
    pub jurisdiction: String,
    pub tax_type: TaxType,
    pub taxable_amount: i64,
    pub tax_amount: i64,
    pub effective_rate: f64,
    /// Treaty benefit applied.
    pub treaty_benefit: Option<TreatyBenefit>,
    pub computed_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TreatyBenefit {
    pub treaty_partner: String,
    pub standard_rate: f64,
    pub treaty_rate: f64,
    pub savings: i64,
}

/// Tax engine trait.
#[async_trait::async_trait]
pub trait TaxEngine: Send + Sync {
    /// Calculate tax for a taxable event.
    async fn calculate(&self, event: &TaxableEvent) -> Result<Vec<TaxCalculation>, TaxError>;
    /// Get applicable tax rules for a jurisdiction.
    async fn rules(&self, jurisdiction: &str) -> Result<TaxJurisdiction, TaxError>;
    /// Check for treaty benefits between jurisdictions.
    async fn treaty_check(&self, from: &str, to: &str) -> Result<Option<TreatyBenefit>, TaxError>;
}

#[derive(Debug, thiserror::Error)]
pub enum TaxError {
    #[error("jurisdiction not found: {0}")]
    JurisdictionNotFound(String),
    #[error("tax calculation error: {0}")]
    CalculationError(String),
    #[error("no treaty found between {from} and {to}")]
    NoTreaty { from: String, to: String },
}
