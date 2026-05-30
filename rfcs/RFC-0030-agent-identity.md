# RFC-0030: Universal Agent Identity (UAI)

**Status:** Draft  
**Created:** 2026-05-30  
**Layer:** Identity (`ss-identity`)  

## 1. Abstract

This RFC defines the Universal Agent Identity (UAI), the persistent cryptographic identity standard for agents, organizations, and robots operating within SovereignStack. UAI establishes trust, reputation, and verifiable provenance without relying on centralized identity providers or global blockchains.

## 2. Motivation

In a network of millions of autonomous sessions, trusting the source of an artifact, memory, or capability is critical. Traditional AI systems lack persistent identity—a model instance spun up today has no memory or reputation tied to yesterday's instance. UAI anchors an agent's history and reputation to a cryptographic key pair.

## 3. Specification

### 3.1 Cryptographic Foundation

All SovereignStack identities are anchored by an **Ed25519 key pair**.
- **Public Key:** Broadcast to the network inside an Identity Document. Used by peers to verify signatures.
- **Private Key:** Held securely by the node operating the agent. Used to sign events, artifacts, and capability advertisements.

### 3.2 The Identity Document

Agents broadcast an Identity Document to the network. This document is serialized as JSON and must be signed by the agent's private key.

```json
{
  "uri": "agent://researcher-1",
  "name": "researcher-1",
  "identity_type": "agent",
  "public_key": "ed25519:e45b...89df",
  "capabilities": ["legal_review", "data_analysis"],
  "created_at": "2026-05-30T10:00:00Z",
  "jurisdiction": {
    "region": "EU",
    "regulation": "GDPR",
    "allow_export": false,
    "replication_policy": "trusted_only"
  },
  "active": true
}
```

### 3.3 Sovereign Identity Graph (SIG)

Identities are not isolated. They form a relational graph (SIG):
- An `org://` signs a delegation certificate granting an `agent://` permission to act on its behalf.
- An `agent://` signs a trust attestation for another `agent://`.

### 3.4 Trust Profiles and Reputation

Trust is multi-dimensional and calculated locally by each node based on direct interactions and peer gossip.
The core components of a Trust Profile are:
1. **Accuracy:** How often the agent's outputs pass verification.
2. **Reliability:** Uptime and task completion rate.
3. **Latency:** Historical response times.
4. **Cost:** Resource consumption per task.

## 4. Verification

When Node A receives an `ArtifactPublished` event claiming to be from `agent://research-1`:
1. Node A queries the DHT for the Identity Document of `agent://research-1`.
2. Node A extracts the Ed25519 public key.
3. Node A verifies the cryptographic signature attached to the Event.
4. If verified, Node A updates `agent://research-1`'s Trust Profile.
