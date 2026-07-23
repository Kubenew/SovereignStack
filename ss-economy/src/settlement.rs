//! # Settlement
//!
//! Trade and payment settlement engine for SovereignStack.
//!
//! URI scheme: `settlement://<settlement-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Settlement mechanism.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SettlementMechanism {
    /// Delivery versus Payment — simultaneous exchange.
    DvP,
    /// Free of Payment — delivery without payment leg.
    FoP,
    /// Payment versus Payment — FX settlement.
    PvP,
    /// Multi-lateral netting.
    Netting,
}

/// Settlement status.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SettlementStatus {
    /// Instruction received.
    Instructed,
    /// Matched with counterparty.
    Matched,
    /// Awaiting settlement window.
    Pending,
    /// Partially settled (e.g., netting in progress).
    Partial { settled_percent: u8 },
    /// Fully settled.
    Settled,
    /// Settlement failed.
    Failed { reason: String },
}

/// A settlement instruction.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SettlementInstruction {
    pub id: Uuid,
    pub uri: String,
    /// The trade or payment being settled.
    pub source_uri: String,
    /// Delivering party.
    pub deliverer: String,
    /// Receiving party.
    pub receiver: String,
    /// Asset being delivered (asset://, bond://, etc.).
    pub asset_uri: Option<String>,
    /// Cash amount (if applicable).
    pub cash_amount: Option<i64>,
    /// Cash currency.
    pub cash_currency: Option<String>,
    /// Settlement mechanism.
    pub mechanism: SettlementMechanism,
    /// Intended settlement date.
    pub settlement_date: DateTime<Utc>,
    /// Current status.
    pub status: SettlementStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Netting result for multi-lateral settlement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NettingResult {
    /// Netting group identifier.
    pub group_id: Uuid,
    /// Original gross obligations.
    pub gross_count: usize,
    /// Net obligations after netting.
    pub net_count: usize,
    /// Net positions per participant.
    pub net_positions: Vec<NetPosition>,
}

/// A net position for one participant.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetPosition {
    pub participant: String,
    pub net_amount: i64,
    pub currency: String,
}

/// Settlement engine trait.
#[async_trait::async_trait]
pub trait SettlementEngine: Send + Sync {
    /// Submit a settlement instruction.
    async fn submit(&self, instruction: SettlementInstruction) -> Result<SettlementInstruction, SettlementError>;
    /// Match settlement instructions between counterparties.
    async fn match_instructions(&self, ids: Vec<Uuid>) -> Result<Vec<SettlementInstruction>, SettlementError>;
    /// Execute netting across a group of instructions.
    async fn net(&self, group: Vec<Uuid>) -> Result<NettingResult, SettlementError>;
    /// Query settlement status.
    async fn status(&self, id: Uuid) -> Result<SettlementInstruction, SettlementError>;
}

#[derive(Debug, thiserror::Error)]
pub enum SettlementError {
    #[error("instruction not found: {0}")]
    NotFound(Uuid),
    #[error("matching failed: {0}")]
    MatchingFailed(String),
    #[error("settlement failed: {0}")]
    SettlementFailed(String),
    #[error("netting impossible: {0}")]
    NettingImpossible(String),
}
