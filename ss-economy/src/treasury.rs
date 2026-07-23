//! # Treasury
//!
//! Treasury and liquidity management for SovereignStack.
//!
//! URI scheme: `treasury://<account-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Treasury account type.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TreasuryAccountType {
    /// Operating cash account.
    Operating,
    /// Reserve account.
    Reserve,
    /// Nostro account (held at another institution).
    Nostro,
    /// Vostro account (held for another institution).
    Vostro,
    /// Escrow account.
    Escrow,
    /// Collateral account.
    Collateral,
}

/// A treasury account.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TreasuryAccount {
    pub id: Uuid,
    pub uri: String,
    /// Owner identity (company://, bank://).
    pub owner: String,
    pub account_type: TreasuryAccountType,
    /// ISO 4217 currency code.
    pub currency: String,
    /// Current balance in smallest unit.
    pub balance: i64,
    /// Available balance (after holds/reserves).
    pub available_balance: i64,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// A cash position across currencies.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CashPosition {
    pub entity: String,
    pub positions: Vec<CurrencyPosition>,
    pub as_of: DateTime<Utc>,
}

/// Position in a single currency.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CurrencyPosition {
    pub currency: String,
    pub balance: i64,
    pub projected_inflows: i64,
    pub projected_outflows: i64,
    pub net_position: i64,
}

/// A liquidity pool for shared funding.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquidityPool {
    pub id: Uuid,
    pub uri: String,
    pub name: String,
    pub currency: String,
    pub total_liquidity: i64,
    pub available_liquidity: i64,
    pub participants: Vec<String>,
}

/// A funding request against a liquidity pool.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FundingRequest {
    pub id: Uuid,
    pub requester: String,
    pub pool_id: Uuid,
    pub amount: i64,
    pub purpose: String,
    pub status: FundingStatus,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FundingStatus {
    Requested,
    Approved,
    Funded,
    Rejected { reason: String },
}

/// Treasury manager trait.
#[async_trait::async_trait]
pub trait TreasuryManager: Send + Sync {
    /// Get cash position for an entity.
    async fn cash_position(&self, entity: &str) -> Result<CashPosition, TreasuryError>;
    /// Transfer between treasury accounts.
    async fn transfer(&self, from: Uuid, to: Uuid, amount: i64) -> Result<(), TreasuryError>;
    /// Request funding from a liquidity pool.
    async fn request_funding(&self, request: FundingRequest) -> Result<FundingRequest, TreasuryError>;
}

#[derive(Debug, thiserror::Error)]
pub enum TreasuryError {
    #[error("account not found: {0}")]
    AccountNotFound(Uuid),
    #[error("insufficient balance")]
    InsufficientBalance,
    #[error("pool not found: {0}")]
    PoolNotFound(Uuid),
    #[error("funding rejected: {0}")]
    FundingRejected(String),
}
