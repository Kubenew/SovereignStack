# RFC-0056: Search Inference Protocol

**Status:** Draft  
**Layer:** Intelligence (cross-cutting with Provenance and Governance)  
**Depends on:** RFC-0001 (Sovereign Object Model), RFC-0013 (Provenance Graph), RFC-0020 (Policy Enforcement)  

## Abstract

This RFC defines the `search://` URI scheme, establishing a standard for auditable inference-time search processes such as Monte Carlo Tree Search (MCTS), beam search, and agentic retrieval. By serialising internal search states, transition probabilities, heuristic scores, and step-by-step reasoning into cryptographically verifiable objects, SovereignStack transitions advanced autonomous reasoning from black-box LLM calls to transparent, governable infrastructure.

## Motivation

As autonomous systems scale in capability, their actions are increasingly driven by complex internal search procedures rather than simple sequential generation. In mission-critical environments (finance, defense, healthcare), a black-box answer is insufficient; the node must be able to justify *how* it arrived at a conclusion, which branches it considered, and why it discarded alternatives.

Without a standardised protocol for capturing this process:
1. **Audits are impossible:** Certification labs cannot verify that an agent properly evaluated safety constraints.
2. **Governance is blind:** Policies cannot intervene mid-search if the agent explores a prohibited cognitive branch.
3. **Replayability is lost:** Post-incident forensics cannot reconstruct the agent's internal state.

The Search Inference Protocol (`search://`) solves this by treating cognitive search as a first-class, addressable, and verifiable resource.

## Specification

### 1. The `search://` URI Scheme

Every inference search process, whether a single branching thought or a million-node MCTS, is assigned a unique identifier.

**Format:**
```abnf
search-uri   = "search://" agent-id "/" search-id [ "/" node-id ]
agent-id     = did-string / uuid
search-id    = uuid / hash
node-id      = path-string
```

**Examples:**
- `search://did:sov:12345/search-8f92a` (The root search object)
- `search://did:sov:12345/search-8f92a/branch-A/node-3` (A specific state within the search tree)

### 2. Search Object Primitives

A `search://` object is a Merkle DAG representing the search space. Each node in the DAG MUST contain:

1. **State Snapshot:** A compressed or delta-encoded representation of the agent's context window at that step.
2. **Transition Probability:** The model-assigned likelihood of this step.
3. **Heuristic Score (Value):** The reward or value metric assigned to this branch (e.g., Q-value in MCTS).
4. **Human-Interpretable Summary:** A mandatory 1-3 sentence summary of what the branch represents.
5. **Cryptographic Signature:** The node's hash, signed by the `ss-reason` runtime enclave.

### 3. Integration with `ss-reason`

The `ss-reason` crate manages the lifecycle of a `search://` object:

1. **Initialization:** When an agent begins a complex reasoning task, `ss-reason` mints a new `search-id`.
2. **Streaming:** As the model yields tokens or generates branches, `ss-reason` constructs the Merkle DAG in real-time.
3. **Policy Hooks:** Before committing a high-value node to the tree, `ss-reason` fires an event to `ss-policy`. If the branch violates a constraint (e.g., simulating a cyberattack), the branch is pruned.
4. **Finalization:** The search concludes, the optimal path is selected, and the entire DAG is sealed and hashed.

### 4. Replay and Auditability

For Level 4 Advanced Autonomous Systems certification, a node must prove that its reasoning processes are verifiable.

A certification lab can take a sealed `search://` object and:
1. Verify all cryptographic signatures against the agent's public key.
2. Reconstruct the exact search tree.
3. Read the human-interpretable summaries to understand the considered alternatives.
4. Confirm that rejected branches were correctly penalized by the heuristic value function.

## Security Considerations

- **State Exhaustion:** A runaway search process could generate billions of nodes, exhausting memory. `ss-reason` MUST enforce strict bounds on `search://` depth and width.
- **Confidentiality:** Search trees may contain highly sensitive working memory. They MUST be encrypted at rest and access-controlled via `ss-capability`.
- **Enclave Tampering:** To prevent an agent from rewriting its own search history post-facto, `search://` objects SHOULD be generated inside a secure enclave (e.g., AWS Nitro) and anchored to an external hardware root of trust.

## Future Evolution

Subsequent extensions to this protocol may define federated search (`ss-swarm`), allowing multiple nodes to collaboratively explore a single `search://` tree via weightless state sharing.
