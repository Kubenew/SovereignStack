//! Local Content-Addressed Storage implementation.

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

use ss_crypto::hash::ContentHash;
use ss_core::error::{Error, Result};

/// An in-memory Content-Addressed Store.
///
/// In a production environment, this would be backed by the filesystem
/// or a key-value store (like RocksDB or Sled).
#[derive(Clone)]
pub struct CasStore {
    // Map of hash -> raw bytes
    store: Arc<RwLock<HashMap<ContentHash, Vec<u8>>>>,
}

impl CasStore {
    /// Create a new in-memory CAS.
    pub fn new() -> Self {
        Self {
            store: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Store data and return its content hash.
    pub async fn put(&self, data: &[u8]) -> ContentHash {
        let hash = ContentHash::compute(data);
        let mut store = self.store.write().await;
        // Optimization: only insert if it doesn't exist
        if !store.contains_key(&hash) {
            store.insert(hash.clone(), data.to_vec());
        }
        hash
    }

    /// Retrieve data by its content hash.
    pub async fn get(&self, hash: &ContentHash) -> Result<Vec<u8>> {
        let store = self.store.read().await;
        store
            .get(hash)
            .cloned()
            .ok_or_else(|| Error::ContentNotFound(hash.to_string()))
    }

    /// Check if a hash exists in the store.
    pub async fn exists(&self, hash: &ContentHash) -> bool {
        let store = self.store.read().await;
        store.contains_key(hash)
    }

    /// Get the total number of objects in the store.
    pub async fn len(&self) -> usize {
        let store = self.store.read().await;
        store.len()
    }
}

impl Default for CasStore {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn put_and_get() {
        let cas = CasStore::new();
        let data = b"immutable knowledge";
        
        let hash = cas.put(data).await;
        assert!(cas.exists(&hash).await);
        
        let retrieved = cas.get(&hash).await.unwrap();
        assert_eq!(retrieved, data);
    }

    #[tokio::test]
    async fn get_nonexistent_fails() {
        let cas = CasStore::new();
        let hash = ContentHash::compute(b"never stored");
        
        assert!(!cas.exists(&hash).await);
        assert!(cas.get(&hash).await.is_err());
    }

    #[tokio::test]
    async fn duplicate_put_is_idempotent() {
        let cas = CasStore::new();
        let data = b"data";
        
        cas.put(data).await;
        assert_eq!(cas.len().await, 1);
        
        cas.put(data).await;
        assert_eq!(cas.len().await, 1); // length shouldn't change
    }
}
