//! Temporal types for SovereignStack.
//!
//! Every memory object in SovereignStack has temporal validity,
//! supporting the Temporal Intelligence pattern where objects
//! have `valid_from` and `valid_until` windows.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fmt;

/// A point-in-time timestamp using UTC.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct Timestamp(DateTime<Utc>);

impl Timestamp {
    /// Create a timestamp for the current moment.
    pub fn now() -> Self {
        Self(Utc::now())
    }

    /// Create a timestamp from a UTC DateTime.
    pub fn from_utc(dt: DateTime<Utc>) -> Self {
        Self(dt)
    }

    /// Returns the inner DateTime<Utc>.
    pub fn as_datetime(&self) -> &DateTime<Utc> {
        &self.0
    }

    /// Returns the Unix timestamp in seconds.
    pub fn unix_secs(&self) -> i64 {
        self.0.timestamp()
    }
}

impl fmt::Display for Timestamp {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0.to_rfc3339())
    }
}

impl Default for Timestamp {
    fn default() -> Self {
        Self::now()
    }
}

/// A temporal validity window for memory objects and knowledge.
///
/// Implements Future-Proof Addition #6: Temporal Intelligence.
/// Every memory object gets a validity window, critical for
/// long-lived autonomous systems.
///
/// # Examples
///
/// ```rust
/// use ss_core::timestamp::TemporalWindow;
/// use ss_core::Timestamp;
///
/// let window = TemporalWindow::from_now();
/// assert!(window.is_valid_now());
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemporalWindow {
    /// When this object becomes valid.
    pub valid_from: Timestamp,
    /// When this object expires (None = never expires).
    pub valid_until: Option<Timestamp>,
    /// When this object was created.
    pub created_at: Timestamp,
    /// When this object was last modified.
    pub modified_at: Timestamp,
}

impl TemporalWindow {
    /// Create a window that is valid from now with no expiration.
    pub fn from_now() -> Self {
        let now = Timestamp::now();
        Self {
            valid_from: now,
            valid_until: None,
            created_at: now,
            modified_at: now,
        }
    }

    /// Create a window with a specific expiration.
    pub fn with_expiration(valid_until: Timestamp) -> Self {
        let now = Timestamp::now();
        Self {
            valid_from: now,
            valid_until: Some(valid_until),
            created_at: now,
            modified_at: now,
        }
    }

    /// Check if this window is currently valid.
    pub fn is_valid_now(&self) -> bool {
        let now = Timestamp::now();
        self.is_valid_at(&now)
    }

    /// Check if this window is valid at a specific timestamp.
    pub fn is_valid_at(&self, at: &Timestamp) -> bool {
        if at < &self.valid_from {
            return false;
        }
        match &self.valid_until {
            Some(until) => at <= until,
            None => true,
        }
    }

    /// Returns true if this window has expired.
    pub fn is_expired(&self) -> bool {
        match &self.valid_until {
            Some(until) => &Timestamp::now() > until,
            None => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn timestamp_now() {
        let ts = Timestamp::now();
        assert!(ts.unix_secs() > 0);
    }

    #[test]
    fn temporal_window_from_now_is_valid() {
        let window = TemporalWindow::from_now();
        assert!(window.is_valid_now());
        assert!(!window.is_expired());
    }

    #[test]
    fn temporal_window_display() {
        let ts = Timestamp::now();
        let display = ts.to_string();
        assert!(display.contains("T")); // ISO 8601 format
    }
}
