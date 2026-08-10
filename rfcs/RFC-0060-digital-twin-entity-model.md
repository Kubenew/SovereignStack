# RFC-0060: Digital Twin Entity Model

**Status:** Draft  
**Authors:** SovereignStack Core Team  
**Created:** 2026-07-23  
**Related:** [RFC-0001](RFC-0001-core-object-model.md) · [RFC-0028](RFC-0028-digital-twin-sync.md) · [RFC-0029](RFC-0029-intelligence-economy.md)

---

## Abstract

This RFC introduces a generalized **Digital Twin Entity Model** for SovereignStack. While RFC-0028 covers synchronization of device-centric twins (`robot://`), this RFC defines a broader class of entity-centric digital twins that represent real-world persons, organizations, financial instruments, facilities, and assets within the Sovereign Intelligence Network.

Every digital twin is a first-class sovereign object that owns its identity, policies, capabilities, provenance, events, memory, and economic state.

---

## Motivation

SovereignStack's architecture is currently agent-centric. Agents perform reasoning, hold sessions, and produce artifacts. However, real-world deployments require representing **entities** that are not agents but are acted upon, governed, and tracked:

- A **person** has identity, financial accounts, health records, and compliance obligations
- A **company** has subsidiaries, portfolios, regulatory filings, and counterparty relationships
- A **bond** has an issuer, maturity schedule, coupon payments, and credit ratings
- A **factory** has production lines, quality metrics, maintenance schedules, and supply chain links

These entities need the same sovereignty guarantees as agents: addressability, verifiability, portability, and auditability.

---

## URI Schemes

### Core Twin Schemes

| Scheme | Description | Example |
|--------|-------------|---------|
| `person://` | Natural person | `person://alice-j-doe` |
| `company://` | Corporate entity | `company://acme-corp` |
| `bank://` | Financial institution | `bank://eu-central-bank` |
| `factory://` | Manufacturing facility | `factory://munich-plant-7` |
| `hospital://` | Healthcare institution | `hospital://charite-berlin` |
| `vehicle://` | Vehicle / autonomous platform | `vehicle://fleet-42/truck-009` |
| `portfolio://` | Investment portfolio | `portfolio://pension-fund-eu/balanced` |
| `fund://` | Investment fund | `fund://sovereign-wealth-no` |
| `bond://` | Debt instrument | `bond://de-bund-2035` |
| `asset://` | Tokenized real-world asset | `asset://tokenized/real-estate/berlin-01` |

### Relationship to Existing Schemes

- `robot://` (RFC-0011) remains for physical device telemetry bridging via `ss-twin`
- `twin://` (Evolution & Provenance) remains for agent candidate twins
- `identity://` remains for stable identity references
- The new schemes above are **entity twins** — they represent the entity itself, not a candidate or shadow

---

## Entity Model

Every digital twin, regardless of scheme, conforms to the following entity model:

```
┌─────────────────────────────────────────────────────┐
│                   Digital Twin                       │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  Identity    │  │  Policy     │  │ Capability │  │
│  │             │  │             │  │            │  │
│  │ DID / UAI   │  │ Governance  │  │ Permissions│  │
│  │ X.509 chain │  │ Compliance  │  │ Delegations│  │
│  │ KYC status  │  │ Jurisdiction│  │ Role-based │  │
│  └─────────────┘  └─────────────┘  └────────────┘  │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  Provenance │  │  Events     │  │  Memory    │  │
│  │             │  │             │  │            │  │
│  │ Lineage     │  │ Lifecycle   │  │ State      │  │
│  │ Audit trail │  │ Transitions │  │ History    │  │
│  │ Signatures  │  │ Telemetry   │  │ Snapshots  │  │
│  └─────────────┘  └─────────────┘  └────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │              Economic State                   │   │
│  │                                              │   │
│  │  Balances · Positions · Obligations          │   │
│  │  Credit ratings · Risk scores · Valuations   │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Identity Layer

Each twin has a stable, cryptographically anchored identity:

```rust
pub struct TwinIdentity {
    /// Primary URI (e.g., person://alice-j-doe)
    pub uri: SovereignUri,
    /// Decentralized Identifier (DID)
    pub did: Option<String>,
    /// Universal Agent Identity (if also an agent)
    pub uai: Option<String>,
    /// X.509 certificate chain
    pub certificates: Vec<Certificate>,
    /// KYC/AML verification status
    pub kyc_status: Option<KycStatus>,
    /// Creation timestamp
    pub created_at: Timestamp,
    /// Last modified timestamp
    pub updated_at: Timestamp,
}
```

### Policy Layer

Governance rules and compliance obligations attached to the twin:

```rust
pub struct TwinPolicy {
    /// Applicable policies (policy:// references)
    pub policies: Vec<SovereignUri>,
    /// Jurisdictional bindings
    pub jurisdictions: Vec<Jurisdiction>,
    /// Compliance framework mappings (ISO 42001, SOC 2, HIPAA, etc.)
    pub compliance_frameworks: Vec<ComplianceFramework>,
    /// Data residency constraints
    pub data_residency: Vec<DataResidencyRule>,
}
```

### Capability Layer

```rust
pub struct TwinCapabilities {
    /// Granted capabilities (capability:// tokens)
    pub granted: Vec<CapabilityToken>,
    /// Delegated capabilities (capability chains)
    pub delegated: Vec<CapabilityDelegation>,
    /// Role bindings
    pub roles: Vec<RoleBinding>,
}
```

### Provenance Layer

```rust
pub struct TwinProvenance {
    /// Full lineage chain
    pub lineage: Vec<ProvenanceEntry>,
    /// Cryptographic signatures over state transitions
    pub signatures: Vec<Signature>,
    /// Audit evidence packages
    pub evidence: Vec<SovereignUri>,
}
```

### Event Layer

```rust
pub struct TwinEventLog {
    /// Lifecycle events (creation, modification, archival)
    pub lifecycle: Vec<LifecycleEvent>,
    /// State transition events
    pub transitions: Vec<TransitionEvent>,
    /// External events (telemetry, market data, regulatory filings)
    pub external: Vec<ExternalEvent>,
}
```

### Memory Layer

```rust
pub struct TwinMemory {
    /// Current state snapshot
    pub current_state: serde_json::Value,
    /// State history (content-addressed snapshots)
    pub history: Vec<SovereignUri>,
    /// Attached knowledge objects
    pub knowledge: Vec<SovereignUri>,
}
```

### Economic State Layer

```rust
pub struct TwinEconomicState {
    /// Account balances
    pub balances: Vec<Balance>,
    /// Open positions
    pub positions: Vec<Position>,
    /// Outstanding obligations
    pub obligations: Vec<Obligation>,
    /// Credit ratings
    pub credit_ratings: Vec<CreditRating>,
    /// Risk scores
    pub risk_scores: Vec<RiskScore>,
    /// Valuations
    pub valuations: Vec<Valuation>,
}
```

---

## Lifecycle

```
Created → Active → Suspended → Archived → Deleted
                 ↗            ↙
              Reactivated
```

| State | Description |
|-------|-------------|
| `Created` | Twin registered, identity established, not yet active |
| `Active` | Twin is live, accepting events, state is mutable |
| `Suspended` | Temporarily frozen (regulatory hold, investigation) |
| `Archived` | Read-only, retained for compliance/audit |
| `Deleted` | Tombstone record, provenance preserved |

All transitions emit events to the Sovereign Event Bus and are recorded in the provenance chain.

---

## Federation

Digital twins follow the same federation model as other SovereignStack objects:

1. **Local-first**: Twin state is authoritative at the owning node
2. **Selective replication**: Specific facets can be replicated to federation peers
3. **Jurisdictional gating**: Data residency rules control cross-border visibility
4. **Capability-gated access**: Federated nodes require capability tokens to read/write twin state

---

## Relationship to ss-twin and ss-economy

| Crate | Focus | Schemes |
|-------|-------|---------|
| `ss-twin` | Physical device bridging, sensors, actuators | `robot://` |
| `ss-economy` | Financial primitives, markets, accounting | `payment://`, `settlement://`, etc. |
| Entity Model (this RFC) | Universal digital twin envelope | `person://`, `company://`, `bank://`, etc. |

The Entity Model provides the **envelope** (identity, policy, capabilities, provenance, events, memory, economic state). Domain-specific crates (`ss-twin` for IoT, `ss-economy` for finance) provide the **content** within those envelopes.

---

## Conformance

Implementations supporting Digital Twin Objects MUST:

1. Resolve all 10 core twin URI schemes
2. Implement the 7-facet entity model (identity, policy, capabilities, provenance, events, memory, economic state)
3. Emit lifecycle events for all state transitions
4. Support content-addressed state snapshots
5. Enforce capability-based access control on all twin operations

---

## References

- [RFC-0001: Sovereign Object Model](RFC-0001-core-object-model.md)
- [RFC-0002: URI Standard](RFC-0002-uri-resolution.md)
- [RFC-0011: Identity & DID Resolution](RFC-0011-identity-did-resolution.md)
- [RFC-0028: Digital Twin Synchronization](RFC-0028-digital-twin-sync.md)
- [RFC-0029: Intelligence Economy Primitives](RFC-0029-intelligence-economy.md)
- [Compliance Framework](../docs/compliance/index.md)
