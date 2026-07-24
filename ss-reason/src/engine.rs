use crate::search::{SearchNode, SearchTree};
use async_trait::async_trait;

/// The core interface for a Search Inference Engine.
/// This trait defines the lifecycle hooks required to implement RFC-0056 (Search Inference Protocol),
/// managing the creation, expansion, and finalization of `search://` object trees.
#[async_trait]
pub trait SearchEngine: Send + Sync {
    /// Initializes a new search process for a given agent.
    /// Returns the newly minted `SearchTree` rooted at `initial_state`.
    async fn initialize_search(
        &self,
        agent_id: String,
        search_id: String,
        initial_state: SearchNode,
    ) -> Result<SearchTree, String>;

    /// Adds a new branch (child node) to an existing search tree.
    /// In a fully integrated SovereignStack node, this method should hook into `ss-policy`
    /// to ensure the new branch does not violate any governance constraints before appending it.
    async fn add_branch(
        &self,
        tree: &mut SearchTree,
        parent_id: &str,
        child_node: SearchNode,
    ) -> Result<(), String>;

    /// Finalizes the search tree, preventing any further branches from being added.
    /// This seals the `search://` object and makes it available for audit or playback.
    async fn finalize_search(&self, tree: &mut SearchTree) -> Result<(), String>;
}

/// A default, in-memory implementation of the SearchEngine for testing or light workloads.
pub struct InMemorySearchEngine;

#[async_trait]
impl SearchEngine for InMemorySearchEngine {
    async fn initialize_search(
        &self,
        agent_id: String,
        search_id: String,
        initial_state: SearchNode,
    ) -> Result<SearchTree, String> {
        Ok(SearchTree::new(agent_id, search_id, initial_state))
    }

    async fn add_branch(
        &self,
        tree: &mut SearchTree,
        parent_id: &str,
        child_node: SearchNode,
    ) -> Result<(), String> {
        tree.add_node(parent_id, child_node)
    }

    async fn finalize_search(&self, tree: &mut SearchTree) -> Result<(), String> {
        tree.finalize();
        Ok(())
    }
}
