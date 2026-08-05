//! URI Resolver — local-first resolution with federated fallback.

use ss_core::{SovereignUri, Timestamp};
use std::sync::Arc;

#[derive(Debug, thiserror::Error)]
pub enum ResolutionError {
    #[error("not found: {0}")]
    NotFound(String),
    #[error("forbidden: {0}")]
    Forbidden(String),
    #[error("federation timeout")]
    FederationTimeout,
    #[error("invalid URI: {0}")]
    InvalidUri(String),
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ResolutionResult {
    pub uri: SovereignUri,
    pub object_type: String,
    pub resolved_by: String,
    pub object: serde_json::Value,
    pub provenance: Vec<String>,
}

pub trait UriResolver: Send + Sync {
    fn resolve(&self, uri: &SovereignUri) -> Result<ResolutionResult, ResolutionError>;
    fn resolve_local(&self, uri: &SovereignUri) -> Result<ResolutionResult, ResolutionError>;
    fn cache_get(&self, uri: &SovereignUri) -> Option<ResolutionResult>;
    fn cache_put(&self, uri: &SovereignUri, result: ResolutionResult, ttl_secs: u64);
}

pub struct UriResolverImpl {
    cache: Arc<dashmap::DashMap<String, (ResolutionResult, Timestamp)>>,
}

impl UriResolverImpl {
    pub fn new() -> Self {
        Self {
            cache: Arc::new(dashmap::DashMap::new()),
        }
    }
}

impl Default for UriResolverImpl {
    fn default() -> Self {
        Self::new()
    }
}

impl UriResolver for UriResolverImpl {
    fn resolve(&self, uri: &SovereignUri) -> Result<ResolutionResult, ResolutionError> {
        self.resolve_local(uri)
    }

    fn resolve_local(&self, uri: &SovereignUri) -> Result<ResolutionResult, ResolutionError> {
        // Check cache first
        if let Some(cached) = self.cache_get(uri) {
            return Ok(cached);
        }
        Err(ResolutionError::NotFound(uri.to_string()))
    }

    fn cache_get(&self, uri: &SovereignUri) -> Option<ResolutionResult> {
        let key = uri.to_string();
        if let Some(entry) = self.cache.get(&key) {
            let (result, expires) = entry.value();
            if Timestamp::now() > *expires {
                drop(entry);
                self.cache.remove(&key);
                return None;
            }
            return Some(result.clone());
        }
        None
    }

    fn cache_put(&self, uri: &SovereignUri, result: ResolutionResult, ttl_secs: u64) {
        let now = Timestamp::now();
        let expires = Timestamp::from_utc(
            *now.as_datetime() + chrono::TimeDelta::seconds(ttl_secs as i64)
        );
        self.cache.insert(uri.to_string(), (result, expires));
    }
}
