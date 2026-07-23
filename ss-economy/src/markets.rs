//! # Markets
//!
//! Market primitives: order books, trading, and market data for SovereignStack.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Order side.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Side {
    Buy,
    Sell,
}

/// Order type.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderType {
    Market,
    Limit { price: i64 },
    StopLoss { trigger_price: i64 },
    StopLimit { trigger_price: i64, limit_price: i64 },
}

/// Order status.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum OrderStatus {
    New,
    PartiallyFilled { filled_quantity: u64 },
    Filled,
    Cancelled,
    Rejected { reason: String },
    Expired,
}

/// Time in force.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TimeInForce {
    /// Good till cancelled.
    GTC,
    /// Immediate or cancel.
    IOC,
    /// Fill or kill.
    FOK,
    /// Good for the day.
    Day,
    /// Good till date.
    GTD { expiry: DateTime<Utc> },
}

/// An order on an order book.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    pub id: Uuid,
    pub instrument_uri: String,
    pub trader: String,
    pub side: Side,
    pub order_type: OrderType,
    pub quantity: u64,
    pub filled_quantity: u64,
    pub time_in_force: TimeInForce,
    pub status: OrderStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// A completed trade.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub id: Uuid,
    pub instrument_uri: String,
    pub buyer: String,
    pub seller: String,
    pub price: i64,
    pub quantity: u64,
    pub buy_order_id: Uuid,
    pub sell_order_id: Uuid,
    pub executed_at: DateTime<Utc>,
}

/// A price quote.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Quote {
    pub instrument_uri: String,
    pub bid: i64,
    pub ask: i64,
    pub bid_size: u64,
    pub ask_size: u64,
    pub last_price: i64,
    pub volume_24h: u64,
    pub timestamp: DateTime<Utc>,
}

/// Market data snapshot.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub instrument_uri: String,
    pub open: i64,
    pub high: i64,
    pub low: i64,
    pub close: i64,
    pub volume: u64,
    pub vwap: Option<i64>,
    pub period_start: DateTime<Utc>,
    pub period_end: DateTime<Utc>,
}

/// Exchange / matching engine trait.
#[async_trait::async_trait]
pub trait Exchange: Send + Sync {
    /// Submit an order.
    async fn submit_order(&self, order: Order) -> Result<Order, MarketError>;
    /// Cancel an order.
    async fn cancel_order(&self, order_id: Uuid) -> Result<Order, MarketError>;
    /// Get current quote for an instrument.
    async fn quote(&self, instrument_uri: &str) -> Result<Quote, MarketError>;
    /// Get market data (OHLCV).
    async fn market_data(&self, instrument_uri: &str) -> Result<MarketData, MarketError>;
    /// List recent trades.
    async fn recent_trades(&self, instrument_uri: &str, limit: usize) -> Result<Vec<Trade>, MarketError>;
}

#[derive(Debug, thiserror::Error)]
pub enum MarketError {
    #[error("order not found: {0}")]
    OrderNotFound(Uuid),
    #[error("instrument not found: {0}")]
    InstrumentNotFound(String),
    #[error("order rejected: {0}")]
    OrderRejected(String),
    #[error("market closed")]
    MarketClosed,
}
