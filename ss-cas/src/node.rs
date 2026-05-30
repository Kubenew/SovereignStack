//! Merkle tree structures for memory and artifacts.

use serde::{Deserialize, Serialize};
use ss_crypto::hash::ContentHash;

/// A node in a Merkle tree.
///
/// Merkle trees allow efficient synchronization and verification of state.
/// Instead of syncing a whole database, nodes just compare tree roots.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MerkleNode {
    /// A leaf node holding actual data (referenced by hash).
    Leaf {
        hash: ContentHash,
        size: usize,
    },
    /// An internal node connecting children.
    Node {
        /// Hash of the combined child hashes.
        hash: ContentHash,
        /// Named links to children (e.g., "Context", "Tasks").
        children: std::collections::BTreeMap<String, ContentHash>,
    },
}

impl MerkleNode {
    /// Get the hash of this node.
    pub fn hash(&self) -> &ContentHash {
        match self {
            Self::Leaf { hash, .. } => hash,
            Self::Node { hash, .. } => hash,
        }
    }
}

/// A Merkle tree representing a specific state or memory hierarchy.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleTree {
    pub root_hash: ContentHash,
}

// In a full implementation, there would be methods here to traverse, 
// diff, and construct trees.
