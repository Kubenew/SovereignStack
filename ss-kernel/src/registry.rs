//! Object Registry — local store of all known objects, indexed by URI/type/owner.

use ss_core::{SovereignUri, Timestamp};
use std::sync::Arc;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ObjectEntry {
    pub uri: SovereignUri,
    pub object_type: String,
    pub owner: Option<SovereignUri>,
    pub version: String,
    pub data: serde_json::Value,
    pub created_at: Timestamp,
    pub tags: Vec<String>,
}

pub trait ObjectRegistry: Send + Sync {
    fn store(&self, entry: ObjectEntry);
    fn get(&self, uri: &SovereignUri) -> Option<ObjectEntry>;
    fn delete(&self, uri: &SovereignUri) -> bool;
    fn find_by_type(&self, object_type: &str) -> Vec<ObjectEntry>;
    fn find_by_owner(&self, owner: &SovereignUri) -> Vec<ObjectEntry>;
    fn find_by_tag(&self, tag: &str) -> Vec<ObjectEntry>;
    fn list(&self) -> Vec<ObjectEntry>;
}

pub struct ObjectRegistryImpl {
    by_uri: Arc<dashmap::DashMap<String, ObjectEntry>>,
    by_type: Arc<dashmap::DashMap<String, Vec<String>>>,
    by_owner: Arc<dashmap::DashMap<String, Vec<String>>>,
    by_tag: Arc<dashmap::DashMap<String, Vec<String>>>,
}

impl ObjectRegistryImpl {
    pub fn new() -> Self {
        Self {
            by_uri: Arc::new(dashmap::DashMap::new()),
            by_type: Arc::new(dashmap::DashMap::new()),
            by_owner: Arc::new(dashmap::DashMap::new()),
            by_tag: Arc::new(dashmap::DashMap::new()),
        }
    }
}

impl ObjectRegistry for ObjectRegistryImpl {
    fn store(&self, entry: ObjectEntry) {
        let uri_str = entry.uri.to_string();
        
        // Remove old index entries if updating
        if let Some(old) = self.by_uri.get(&uri_str) {
            let old = old.value();
            if let Some(mut types) = self.by_type.get_mut(&old.object_type) {
                types.retain(|u| u != &uri_str);
            }
            if let Some(ref owner) = old.owner {
                if let Some(mut owners) = self.by_owner.get_mut(&owner.to_string()) {
                    owners.retain(|u| u != &uri_str);
                }
            }
            for tag in &old.tags {
                if let Some(mut tags) = self.by_tag.get_mut(tag) {
                    tags.retain(|u| u != &uri_str);
                }
            }
        }

        self.by_uri.insert(uri_str.clone(), entry.clone());
        self.by_type
            .entry(entry.object_type.clone())
            .or_default()
            .push(uri_str.clone());
        if let Some(ref owner) = entry.owner {
            self.by_owner
                .entry(owner.to_string())
                .or_default()
                .push(uri_str.clone());
        }
        for tag in &entry.tags {
            self.by_tag
                .entry(tag.clone())
                .or_default()
                .push(uri_str.clone());
        }
    }

    fn get(&self, uri: &SovereignUri) -> Option<ObjectEntry> {
        self.by_uri.get(&uri.to_string()).map(|e| e.value().clone())
    }

    fn delete(&self, uri: &SovereignUri) -> bool {
        self.by_uri.remove(&uri.to_string()).is_some()
    }

    fn find_by_type(&self, object_type: &str) -> Vec<ObjectEntry> {
        self.by_type
            .get(object_type)
            .map(|uris| {
                uris.value()
                    .iter()
                    .filter_map(|u| self.by_uri.get(u).map(|e| e.value().clone()))
                    .collect()
            })
            .unwrap_or_default()
    }

    fn find_by_owner(&self, owner: &SovereignUri) -> Vec<ObjectEntry> {
        self.by_owner
            .get(&owner.to_string())
            .map(|uris| {
                uris.value()
                    .iter()
                    .filter_map(|u| self.by_uri.get(u).map(|e| e.value().clone()))
                    .collect()
            })
            .unwrap_or_default()
    }

    fn find_by_tag(&self, tag: &str) -> Vec<ObjectEntry> {
        self.by_tag
            .get(tag)
            .map(|uris| {
                uris.value()
                    .iter()
                    .filter_map(|u| self.by_uri.get(u).map(|e| e.value().clone()))
                    .collect()
            })
            .unwrap_or_default()
    }

    fn list(&self) -> Vec<ObjectEntry> {
        self.by_uri.iter().map(|e| e.value().clone()).collect()
    }
}
