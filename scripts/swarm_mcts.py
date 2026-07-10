"""Monte Carlo Tree Search for agent reasoning branch exploration (ss-swarm)."""
import math
import random
from typing import List, Optional


class MCTSReasoningNode:
    def __init__(self, uri: str, parent: Optional["MCTSReasoningNode"] = None):
        self.uri = uri
        self.parent = parent
        self.children: List["MCTSReasoningNode"] = []
        self.visits = 0
        self.alignment_score = 0.0

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


def select_cognitive_branch(node: MCTSReasoningNode) -> MCTSReasoningNode:
    current = node
    while current.children:
        if not current.is_fully_expanded():
            return current
        current = max(current.children, key=lambda c: c.upper_confidence_bound())
    return current


def expand_agent_fork(node: MCTSReasoningNode, branch_id: int) -> MCTSReasoningNode:
    forked_uri = f"{node.uri}/fork-step-{branch_id}"
    child_node = MCTSReasoningNode(uri=forked_uri, parent=node)
    node.children.append(child_node)
    return child_node


def backpropagate_alignment(node: MCTSReasoningNode, score: float):
    current = node
    while current is not None:
        current.visits += 1
        current.alignment_score += score
        current = current.parent


if __name__ == "__main__":
    root_thought = MCTSReasoningNode(uri="reason://root-agent-decision")
    selected = select_cognitive_branch(root_thought)
    new_fork = expand_agent_fork(selected, branch_id=1)
    simulated_score = random.uniform(0.75, 1.0)
    backpropagate_alignment(new_fork, simulated_score)
    print(f"Root visits: {root_thought.visits}, Branch URI: {new_fork.uri}")
