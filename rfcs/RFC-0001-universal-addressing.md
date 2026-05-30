# RFC-0001: Universal Addressing Scheme

**Status:** Draft  
**Created:** 2026-05-30  
**Layer:** Core (ss-core)  

## 1. Abstract

This RFC defines the Sovereign URI, the universal addressing scheme for all objects within the SovereignStack intelligence network. By making every object—including agents, sessions, artifacts, memories, reasoning chains, and physical devices—globally addressable, SovereignStack provides a uniform foundation for discovery, federation, and auditing.

## 2. Motivation

Traditional applications silo data behind closed APIs or non-transferable database IDs. For a civilization-scale intelligence network to function, objects must be referencable across organizational and network boundaries. 

The Universal Addressing Scheme enables:
- **Federation:** Node A can reference an artifact created by Node B.
- **Provenance:** An output can point precisely to the `agent://` and `model://` that generated it.
- **Routing:** Capability requests can target `capability://` rather than specific IP addresses.

## 3. Specification

A Sovereign URI conforms to the standard URI syntax defined in RFC 3986:

```
scheme://authority/path[?query][#fragment]
```

### 3.1 Registered Schemes

The following schemes are officially registered in the SovereignStack kernel:

| Scheme | Authority | Description |
|---|---|---|
| `agent` | Agent Name | Persistent identity of an AI agent |
| `org` | Org Name | Organizational boundary |
| `session` | Session ID | An active, multiplexed execution session |
| `artifact` | SHA-256 Hash | Immutable output produced by an agent |
| `memory` | Memory ID | A stateful memory object (Tier 0-3) |
| `reason` | Reason ID | An auditable reasoning chain |
| `knowledge` | Domain/Topic | Curated knowledge objects |
| `capability` | Skill Name | Advertised agent capability |
| `workflow` | DAG Name | Intelligence DAG definition |
| `contract` | Contract ID | Verifiable commitment between agents |
| `robot` | Device ID | Digital twin of a physical system |
| `policy` | Policy Name | Machine-readable governance rule |
| `node` | Node ID | A physical or virtual SovereignStack peer |
| `event` | Event ID | An immutable state change record |

### 3.2 Resolution Mechanism

Sovereign URIs are resolved via the Sovereign Name Service (SNS), which operates in three tiers:
1. **Local:** Checked against the node's local memory store or Identity Registry.
2. **Federated:** Resolved via the libp2p Kademlia Distributed Hash Table (DHT).
3. **Global:** Resolved via broadcast capability query (Semantic DNS).

## 4. Examples

- `agent://legal-reviewer-alpha`
- `artifact://sha256:d8a5...9f2c`
- `capability://contract-analysis?language=cs`
- `knowledge://physics/newton-laws/v2.1`

## 5. Security Considerations

URIs themselves carry no trust. To verify the authenticity of an object referenced by a URI, the object must be retrieved and its cryptographic signature verified against the creator's public key (as defined in RFC-0030).
