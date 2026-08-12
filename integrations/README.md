# SovereignStack Integrations

Control-plane integrations prove SovereignStack as the **verifiable trust,
identity, policy, and evidence layer above infrastructure control planes**.

Every integration implements the same five-interface adapter pattern:

| Interface            | Purpose                                                    |
|----------------------|------------------------------------------------------------|
| `identity_mapper`    | Control-plane users/service accounts → `agent://` identities |
| `capability_mapper`  | Control-plane roles → `capability://` grants               |
| `policy_translator`  | `policy://` YAML catalogs → evaluation engine (RFC-0075)   |
| `event_listener`     | Control-plane events → chained provenance entries          |
| provenance + evidence | Tamper-evident chains and independently verifiable packages |

And the same core contract: **identity → capability → policy → provenance →
evidence** — Morpheus (or any control plane) is only contacted when the
governing decision is ALLOW; denials are recorded as evidence too.

## Integrations

| Integration                     | Target                | Profile                       | Status                    |
|---------------------------------|-----------------------|-------------------------------|---------------------------|
| [HPE Morpheus](hpe-morpheus/)   | Morpheus >= 6.0       | OASA-MORPHEUS-CORE-0.1 (L3)   | Conformance tested (CI)   |

Each integration directory is self-contained:

```
integrations/<control-plane>/
├── README.md            # Overview & positioning
├── ARCHITECTURE.md      # Governance pipeline + security properties
├── QUICKSTART.md        # Runnable demo
├── api/                 # Governed client + mock + schemas
├── adapter/             # identity / capability / policy / event mappers
├── policies/            # Example policy catalogs
├── provenance/          # Tamper-evident chains
├── evidence/            # Evidence generation & verification
├── conformance/         # Certification profile + test suite
└── examples/            # End-to-end scenarios
```

## Roadmap

- `integrations/kubernetes/` (future)
- `integrations/vmware/` (future)

## Certification

Each integration targets a machine-verifiable OASA profile
(RFC-0077 format) with its own control IDs (e.g. MOR-001..MOR-010). The
conformance suites are wired into CI as must-pass gates. See the
[OASA certification framework](../../CERTIFICATION.md) for level semantics.
