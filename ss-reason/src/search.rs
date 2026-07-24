use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use ss_core::uri::SovereignUri;
use std::collections::HashMap;

/// Represents the status of a SearchTree.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SearchStatus {
    Active,
    Finalized,
}

/// Represents a single node in a search inference tree (e.g., MCTS or beam search).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchNode {
    /// The unique identifier of this node within the search tree.
    pub node_id: String,
    /// A representation of the agent's context or state at this node.
    pub state_snapshot: String,
    /// The probability of transitioning to this node, assigned by the model.
    pub transition_probability: f32,
    /// The evaluated reward or heuristic value of this branch.
    pub heuristic_score: f32,
    /// A human-interpretable summary of what this branch represents.
    pub human_summary: String,
    /// The IDs of the child nodes branching from this node.
    pub children: Vec<String>,
    /// The cryptographic signature (or hash) of this node.
    pub signature: String,
}

impl SearchNode {
    /// Computes a deterministic SHA-256 hash of the node's contents.
    pub fn compute_hash(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.node_id.as_bytes());
        hasher.update(self.state_snapshot.as_bytes());
        hasher.update(self.transition_probability.to_le_bytes());
        hasher.update(self.heuristic_score.to_le_bytes());
        hasher.update(self.human_summary.as_bytes());
        for child in &self.children {
            hasher.update(child.as_bytes());
        }
        let result = hasher.finalize();
        hex::encode(result)
    }

    /// Signs the node by computing its hash and setting the signature field.
    pub fn sign(&mut self) {
        self.signature = self.compute_hash();
    }
}

/// Represents an entire search inference process, tracking all explored branches.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchTree {
    /// The `search://` URI identifying this specific search process.
    pub search_uri: SovereignUri,
    /// The DID or UUID of the agent performing the search.
    pub agent_id: String,
    /// The ID of the root node of the search tree.
    pub root_node_id: String,
    /// All nodes in the search tree, mapped by their `node_id`.
    pub nodes: HashMap<String, SearchNode>,
    /// The current status of the search.
    pub status: SearchStatus,
}

impl SearchTree {
    /// Creates a new SearchTree with a specific search ID and agent ID.
    pub fn new(agent_id: String, search_id: String, root_node: SearchNode) -> Self {
        let search_uri_str = format!("search://{}/{}", agent_id, search_id);
        let search_uri = SovereignUri::parse(&search_uri_str).unwrap_or_else(|_| {
            // Fallback for when full URI parsing isn't strictly necessary or fails in tests
            SovereignUri::new("search", &format!("{}/{}", agent_id, search_id))
        });
        
        let root_node_id = root_node.node_id.clone();
        let mut nodes = HashMap::new();
        nodes.insert(root_node_id.clone(), root_node);

        Self {
            search_uri,
            agent_id,
            root_node_id,
            nodes,
            status: SearchStatus::Active,
        }
    }

    /// Adds a child node to a specified parent node in the tree.
    pub fn add_node(&mut self, parent_id: &str, mut child_node: SearchNode) -> Result<(), String> {
        if self.status == SearchStatus::Finalized {
            return Err("Cannot add node: SearchTree is finalized".into());
        }

        if !self.nodes.contains_key(parent_id) {
            return Err(format!("Parent node {} not found", parent_id));
        }

        // Ensure child is signed
        if child_node.signature.is_empty() {
            child_node.sign();
        }

        let child_id = child_node.node_id.clone();
        self.nodes.insert(child_id.clone(), child_node);

        // Update the parent's children list
        if let Some(parent) = self.nodes.get_mut(parent_id) {
            parent.children.push(child_id);
            // Re-sign parent since its contents (children) changed
            parent.sign();
        }

        Ok(())
    }

    /// Finalizes the search tree, preventing further modifications.
    pub fn finalize(&mut self) {
        self.status = SearchStatus::Finalized;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_dummy_node(id: &str, summary: &str) -> SearchNode {
        let mut node = SearchNode {
            node_id: id.to_string(),
            state_snapshot: "{}".to_string(),
            transition_probability: 1.0,
            heuristic_score: 0.5,
            human_summary: summary.to_string(),
            children: vec![],
            signature: String::new(),
        };
        node.sign();
        node
    }

    #[test]
    fn test_search_tree_creation() {
        let root = create_dummy_node("root-1", "Initial state");
        let tree = SearchTree::new("agent-123".to_string(), "search-abc".to_string(), root);
        
        assert_eq!(tree.status, SearchStatus::Active);
        assert_eq!(tree.nodes.len(), 1);
        assert_eq!(tree.root_node_id, "root-1");
    }

    #[test]
    fn test_add_node() {
        let root = create_dummy_node("root-1", "Initial state");
        let mut tree = SearchTree::new("agent-123".to_string(), "search-abc".to_string(), root);
        
        let child = create_dummy_node("child-1", "Explored branch A");
        assert!(tree.add_node("root-1", child).is_ok());
        assert_eq!(tree.nodes.len(), 2);
        
        let parent = tree.nodes.get("root-1").unwrap();
        assert!(parent.children.contains(&"child-1".to_string()));
    }

    #[test]
    fn test_hash_determinism() {
        let node1 = create_dummy_node("node-1", "Summary");
        let node2 = create_dummy_node("node-1", "Summary");
        
        assert_eq!(node1.signature, node2.signature);
    }
}
