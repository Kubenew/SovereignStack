//! # Accounting
//!
//! Double-entry accounting ledger for SovereignStack.
//!
//! URI scheme: `account://<ledger-id>/<account>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Account type per accounting standards.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AccountType {
    Asset,
    Liability,
    Equity,
    Revenue,
    Expense,
    ContraAsset,
    ContraLiability,
    ContraEquity,
}

/// Debit or Credit.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EntryDirection {
    Debit,
    Credit,
}

/// A ledger account.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub id: Uuid,
    pub uri: String,
    /// Account code (e.g., "1000", "2100").
    pub code: String,
    pub name: String,
    pub account_type: AccountType,
    pub currency: String,
    /// Current balance.
    pub balance: i64,
    /// Normal balance direction.
    pub normal_balance: EntryDirection,
    /// Parent account for hierarchy.
    pub parent_id: Option<Uuid>,
    pub created_at: DateTime<Utc>,
}

/// A single journal entry line.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JournalEntryLine {
    pub account_id: Uuid,
    pub direction: EntryDirection,
    pub amount: i64,
    pub currency: String,
    pub description: Option<String>,
}

/// A balanced journal entry (debits == credits).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JournalEntry {
    pub id: Uuid,
    /// Source transaction (payment://, settlement://, etc.).
    pub source_uri: Option<String>,
    pub description: String,
    pub lines: Vec<JournalEntryLine>,
    pub posted_at: DateTime<Utc>,
    pub created_by: String,
}

/// Trial balance report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrialBalance {
    pub as_of: DateTime<Utc>,
    pub total_debits: i64,
    pub total_credits: i64,
    pub accounts: Vec<TrialBalanceLine>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrialBalanceLine {
    pub account_id: Uuid,
    pub account_code: String,
    pub account_name: String,
    pub debit_balance: i64,
    pub credit_balance: i64,
}

/// Accounting engine trait.
#[async_trait::async_trait]
pub trait AccountingEngine: Send + Sync {
    /// Create a new account.
    async fn create_account(&self, account: Account) -> Result<Account, AccountingError>;
    /// Post a journal entry (must balance).
    async fn post_entry(&self, entry: JournalEntry) -> Result<JournalEntry, AccountingError>;
    /// Get account balance.
    async fn balance(&self, account_id: Uuid) -> Result<i64, AccountingError>;
    /// Generate trial balance.
    async fn trial_balance(&self, as_of: DateTime<Utc>) -> Result<TrialBalance, AccountingError>;
}

#[derive(Debug, thiserror::Error)]
pub enum AccountingError {
    #[error("account not found: {0}")]
    AccountNotFound(Uuid),
    #[error("journal entry unbalanced: debits={debits}, credits={credits}")]
    Unbalanced { debits: i64, credits: i64 },
    #[error("duplicate account code: {0}")]
    DuplicateCode(String),
}
