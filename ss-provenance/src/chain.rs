use crate::{ProvenanceEntry, ProvenanceError};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceChain {
    pub entries: Vec<ProvenanceEntry>,
    pub root_hash: Option<String>,
}

impl ProvenanceChain {
    pub fn new() -> Self {
        Self {
            entries: Vec::new(),
            root_hash: None,
        }
    }

    pub fn append(&mut self, entry: ProvenanceEntry) -> Result<(), ProvenanceError> {
        // Enforce linkage if not first entry
        if let Some(last) = self.entries.last() {
            let last_hash = last.hash();
            if entry.parent_hash.as_deref() != Some(last_hash.as_str()) {
                return Err(ProvenanceError::BrokenLink {
                    expected: last_hash,
                    found: entry.parent_hash.clone().unwrap_or_default(),
                });
            }
        } else if entry.parent_hash.is_some() {
            return Err(ProvenanceError::BrokenLink {
                expected: "None".to_string(),
                found: entry.parent_hash.clone().unwrap(),
            });
        }

        self.root_hash = Some(entry.hash());
        self.entries.push(entry);
        Ok(())
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }
    
    pub fn len(&self) -> usize {
        self.entries.len()
    }
}

impl Default for ProvenanceChain {
    fn default() -> Self {
        Self::new()
    }
}
