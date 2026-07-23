//! # Payments
//!
//! Payment processing primitives for SovereignStack.
//!
//! URI scheme: `payment://<payment-id>`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// The status of a payment through its lifecycle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PaymentStatus {
    /// Payment instruction created but not yet submitted.
    Pending,
    /// Submitted for processing.
    Submitted,
    /// Authorized by the payer's institution.
    Authorized,
    /// Cleared through the payment network.
    Cleared,
    /// Successfully settled.
    Settled,
    /// Payment failed at any stage.
    Failed { reason: String },
    /// Reversed after settlement.
    Reversed,
    /// Cancelled before settlement.
    Cancelled,
}

/// Supported payment methods.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PaymentMethod {
    /// Bank transfer (SWIFT, SEPA, ACH, Fedwire).
    BankTransfer { network: String },
    /// Card payment (credit/debit).
    Card { network: String, token: String },
    /// Digital wallet.
    Wallet { provider: String },
    /// Tokenized asset transfer.
    TokenizedAsset { asset_uri: String },
    /// Central bank digital currency.
    Cbdc { currency: String },
}

/// A monetary amount with currency.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Money {
    /// Amount in the smallest unit (e.g., cents for USD).
    pub amount: i64,
    /// ISO 4217 currency code (e.g., "USD", "EUR") or asset identifier.
    pub currency: String,
    /// Decimal places for display (e.g., 2 for USD, 8 for BTC).
    pub decimals: u8,
}

/// A payment instruction.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Payment {
    /// Unique payment identifier.
    pub id: Uuid,
    /// Payment URI (e.g., `payment://swift/pacs008-001`).
    pub uri: String,
    /// Payer identity (person://, company://, or agent://).
    pub payer: String,
    /// Payee identity.
    pub payee: String,
    /// Payment amount.
    pub amount: Money,
    /// Payment method.
    pub method: PaymentMethod,
    /// Current status.
    pub status: PaymentStatus,
    /// ISO 20022 message type (e.g., "pacs.008", "pain.001").
    pub iso20022_type: Option<String>,
    /// Reference / remittance information.
    pub reference: Option<String>,
    /// Creation timestamp.
    pub created_at: DateTime<Utc>,
    /// Last update timestamp.
    pub updated_at: DateTime<Utc>,
}

/// A request to initiate a payment.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaymentRequest {
    pub payer: String,
    pub payee: String,
    pub amount: Money,
    pub method: PaymentMethod,
    pub iso20022_type: Option<String>,
    pub reference: Option<String>,
}

/// The payment gateway trait — implemented by payment processors.
#[async_trait::async_trait]
pub trait PaymentGateway: Send + Sync {
    /// Initiate a payment.
    async fn initiate(&self, request: PaymentRequest) -> Result<Payment, PaymentError>;
    /// Query payment status.
    async fn status(&self, payment_id: Uuid) -> Result<Payment, PaymentError>;
    /// Cancel a pending payment.
    async fn cancel(&self, payment_id: Uuid) -> Result<Payment, PaymentError>;
    /// Reverse a settled payment.
    async fn reverse(&self, payment_id: Uuid, reason: String) -> Result<Payment, PaymentError>;
}

/// Errors from payment operations.
#[derive(Debug, thiserror::Error)]
pub enum PaymentError {
    #[error("payment not found: {0}")]
    NotFound(Uuid),
    #[error("insufficient funds")]
    InsufficientFunds,
    #[error("payment method not supported: {0}")]
    UnsupportedMethod(String),
    #[error("authorization failed: {0}")]
    AuthorizationFailed(String),
    #[error("network error: {0}")]
    NetworkError(String),
    #[error("compliance violation: {0}")]
    ComplianceViolation(String),
}
