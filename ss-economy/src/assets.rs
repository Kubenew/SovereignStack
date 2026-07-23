//! # Assets
//!
//! Tokenized asset registry for SovereignStack.
//!
//! URI scheme: `asset://<asset-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Asset classification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AssetClass {
    Equity,
    FixedIncome,
    RealEstate,
    Commodity,
    Currency,
    Cryptocurrency,
    IntellectualProperty,
    Infrastructure,
    Alternative,
    Custom(String),
}

/// Tokenization status.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TokenizationStatus {
    /// Not yet tokenized.
    Physical,
    /// Tokenization in progress.
    InProgress,
    /// Fully tokenized on-chain.
    Tokenized { token_standard: String },
    /// Fractionalized into multiple tokens.
    Fractionalized { total_fractions: u64 },
}

/// A registered asset.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Asset {
    pub id: Uuid,
    pub uri: String,
    pub name: String,
    pub description: String,
    pub asset_class: AssetClass,
    /// Issuer identity (company://, bank://).
    pub issuer: String,
    /// Current custodian.
    pub custodian: Option<String>,
    /// Tokenization status.
    pub tokenization: TokenizationStatus,
    /// Total supply (for tokenized assets).
    pub total_supply: Option<u64>,
    /// Current valuation in base currency.
    pub valuation: Option<i64>,
    /// Valuation currency.
    pub valuation_currency: Option<String>,
    /// ISIN (International Securities Identification Number).
    pub isin: Option<String>,
    /// CUSIP identifier.
    pub cusip: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Asset registry trait.
#[async_trait::async_trait]
pub trait AssetRegistry: Send + Sync {
    /// Register a new asset.
    async fn register(&self, asset: Asset) -> Result<Asset, AssetError>;
    /// Lookup an asset by URI.
    async fn lookup(&self, uri: &str) -> Result<Asset, AssetError>;
    /// List assets by class.
    async fn list_by_class(&self, class: AssetClass) -> Result<Vec<Asset>, AssetError>;
    /// Update asset valuation.
    async fn update_valuation(&self, id: Uuid, valuation: i64, currency: &str) -> Result<Asset, AssetError>;
    /// Transfer asset ownership.
    async fn transfer(&self, id: Uuid, new_custodian: &str) -> Result<Asset, AssetError>;
}

#[derive(Debug, thiserror::Error)]
pub enum AssetError {
    #[error("asset not found: {0}")]
    NotFound(Uuid),
    #[error("asset already registered: {0}")]
    AlreadyRegistered(String),
    #[error("invalid asset class: {0}")]
    InvalidClass(String),
    #[error("tokenization error: {0}")]
    TokenizationError(String),
}
