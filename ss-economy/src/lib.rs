//! # ss-economy
//!
//! Financial Economy Primitives for SovereignStack.
//!
//! This crate provides 12 feature-gated sub-modules that map directly onto
//! real financial institution domains:
//!
//! | Module | Feature | Domain |
//! |--------|---------|--------|
//! | `payments` | `payments` | Payment processing & transfers |
//! | `settlement` | `settlement` | Trade & payment settlement |
//! | `treasury` | `treasury` | Treasury & liquidity management |
//! | `assets` | `assets` | Tokenized asset registry |
//! | `markets` | `markets` | Order books, trading, market data |
//! | `insurance` | `insurance` | Policies, claims, underwriting |
//! | `risk` | `risk` | Risk models, VaR, stress testing |
//! | `derivatives` | `derivatives` | Options, futures, swaps |
//! | `accounting` | `accounting` | Double-entry ledger |
//! | `tax` | `tax` | Tax computation & jurisdiction |
//! | `fin_identity` | `fin_identity` | KYC / AML / sanctions |
//! | `fin_compliance` | `fin_compliance` | Regulatory compliance engine |
//!
//! All modules use `payment://`, `settlement://`, `treasury://`, and related
//! URI schemes defined in RFC-0060 and the URI Standard.

#[cfg(feature = "payments")]
pub mod payments;

#[cfg(feature = "settlement")]
pub mod settlement;

#[cfg(feature = "treasury")]
pub mod treasury;

#[cfg(feature = "assets")]
pub mod assets;

#[cfg(feature = "markets")]
pub mod markets;

#[cfg(feature = "insurance")]
pub mod insurance;

#[cfg(feature = "risk")]
pub mod risk;

#[cfg(feature = "derivatives")]
pub mod derivatives;

#[cfg(feature = "accounting")]
pub mod accounting;

#[cfg(feature = "tax")]
pub mod tax;

#[cfg(feature = "fin_identity")]
pub mod fin_identity;

#[cfg(feature = "fin_compliance")]
pub mod fin_compliance;
