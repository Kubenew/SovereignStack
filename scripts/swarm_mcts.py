"""Monte Carlo Tree Search with kv:// cache-aware node selection."""
import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple


class KvCacheMonitor:
    """Reads kv:// cache utilization metrics from fabric nodes."""

    def __init__(self, kv_endpoint: str = "kv://localhost:6379"):
        self.kv_endpoint = kv_endpoint
        self._node_cache: Dict[str, float] = {}

    def fetch_node_metrics(self) -> Dict[str, float]:
        """Returns {node_uri: cache_load_ratio} for each known node."""
        # In production this reads from the distributed KV store;
        # here we simulate with a random walk.
        nodes = [
            "mem://zcube-a/gpu-001/hbm",
            "mem://zcube-a/gpu-002/hbm",
            "mem://zcube-a/gpu-003/hbm",
        ]
        for node in nodes:
            current = self._node_cache.get(node, 0.5)
            delta = random.uniform(-0.08, 0.08)
            self._node_cache[node] = max(0.0, min(1.0, current + delta))
        return dict(self._node_cache)

    def is_node_available(self, node_uri: str, threshold: float = 0.85) -> bool:
        metrics = self.fetch_node_metrics()
        load = metrics.get(node_uri, 0.0)
        return load < threshold


class MCTSReasoningNode:
    def __init__(self, uri: str, parent: Optional["MCTSReasoningNode"] = None):
        self.uri = uri
        self.parent = parent
        self.children: List["MCTSReasoningNode"] = []
        self.visits = 0
        self.alignment_score = 0.0
        self.assigned_node: Optional[str] = None

    def is_fully_expanded(self) -> bool:
        return len(self.children) >= 4

    def upper_confidence_bound(self, exploration_constant: float = 1.414) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.alignment_score / self.visits
        exploration = exploration_constant * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploitation + exploration

    def capacity_penalized_score(self, cache_monitor: KvCacheMonitor) -> float:
        """Reduces UCT score for nodes whose assigned GPU has high cache load."""
        uct = self.upper_confidence_bound()
        if self.assigned_node and not cache_monitor.is_node_available(
            self.assigned_node
        ):
            return uct * 0.3
        return uct


def select_cognitive_branch(
    node: MCTSReasoningNode,
    cache_monitor: Optional[KvCacheMonitor] = None,
) -> MCTSReasoningNode:
    current = node
    while current.children:
        if not current.is_fully_expanded():
            return current
        if cache_monitor:
            current = max(
                current.children,
                key=lambda c: c.capacity_penalized_score(cache_monitor),
            )
        else:
            current = max(current.children, key=lambda c: c.upper_confidence_bound())
    return current


def select_optimal_node(
    candidate_nodes: List[str], cache_monitor: KvCacheMonitor
) -> Optional[str]:
    """Picks the node with lowest cache load among candidates."""
    metrics = cache_monitor.fetch_node_metrics()
    available = [
        n for n in candidate_nodes if cache_monitor.is_node_available(n)
    ]
    if not available:
        return None
    return min(available, key=lambda n: metrics.get(n, 1.0))


def expand_agent_fork(
    node: MCTSReasoningNode,
    branch_id: int,
    cache_monitor: Optional[KvCacheMonitor] = None,
    candidate_nodes: Optional[List[str]] = None,
) -> MCTSReasoningNode:
    forked_uri = f"{node.uri}/fork-step-{branch_id}"
    child_node = MCTSReasoningNode(uri=forked_uri, parent=node)
    if cache_monitor and candidate_nodes:
        chosen = select_optimal_node(candidate_nodes, cache_monitor)
        child_node.assigned_node = chosen
    node.children.append(child_node)
    return child_node


def backpropagate_alignment(node: MCTSReasoningNode, score: float):
    current = node
    while current is not None:
        current.visits += 1
        current.alignment_score += score
        current = current.parent


if __name__ == "__main__":
    cache_monitor = KvCacheMonitor()
    root_thought = MCTSReasoningNode(uri="reason://root-agent-decision")

    candidate_nodes = [
        "mem://zcube-a/gpu-001/hbm",
        "mem://zcube-a/gpu-002/hbm",
        "mem://zcube-a/gpu-003/hbm",
    ]

    for branch in range(3):
        selected = select_cognitive_branch(root_thought, cache_monitor)
        new_fork = expand_agent_fork(
            selected, branch, cache_monitor, candidate_nodes
        )
        simulated_score = random.uniform(0.75, 1.0)
        backpropagate_alignment(new_fork, simulated_score)

    metrics = cache_monitor.fetch_node_metrics()
    print(f"Root visits: {root_thought.visits}")
    for child in root_thought.children:
        print(
            f"  Branch: {child.uri} -> {child.assigned_node or 'unassigned'}"
        )
    print(f"KV cache metrics: {json.dumps(metrics, indent=2)}")
