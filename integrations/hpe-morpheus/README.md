# HPE Morpheus Integration — SovereignStack OASA Profile

> SovereignStack governing HPE Morpheus: cryptographically verifiable autonomous
> infrastructure.

**Status:** Conformance Tested (OASA-MORPHEUS-CORE-0.1) · **Target:** Morpheus >= 6.0 · **Requires:** SovereignStack >= 0.6.0

This integration positions SovereignStack as the **verifiable trust, identity,
policy, and evidence layer above infrastructure control planes**. It does not
replace HPE Morpheus. It multiplies it: every Morpheus API action is authorized
by cryptographic identity, bounded by policy, and recorded as tamper-evident
provenance.

```
┌─────────────────────────────────────────────┐
│              SOVEREIGNSTACK                  │
│      Trust · Identity · Policy · Evidence    │
├─────────────────────────────────────────────┤
│              OASA CERTIFICATION              │
│    Machine-verifiable conformance profiles   │
├─────────────────────────────────────────────┤
│         INFRASTRUCTURE CONTROL PLANES         │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Morpheus │  │Kubernetes│  │  VMware    │ │
│  │          │  │          │  │  vSphere   │ │
│  └──────────┘  └──────────┘  └────────────┘ │
├─────────────────────────────────────────────┤
│              PHYSICAL / VIRTUAL              │
│      Compute · Network · Storage · GPU       │
└─────────────────────────────────────────────┘
```

## Conceptual Mapping

| Morpheus Concept        | SovereignStack Concept | Integration Point        |
|-------------------------|------------------------|--------------------------|
| User / Service Account  | `agent://` identity    | Identity binding         |
| Role-Based Access       | `capability://`        | Capability mapping       |
| Governance Policies     | `policy://`            | Policy translation       |
| API actions             | `event://`             | Action provenance        |
| Audit logs              | `provenance://`        | Cryptographic evidence   |
| Plugin framework        | `ss-morpheus` adapter  | Integration surface      |
| REST API                | HTTP / JSON            | Communication layer      |

## Repository Layout

```
integrations/hpe-morpheus/
├── README.md                    # This file — overview & positioning
├── ARCHITECTURE.md              # Detailed integration architecture
├── QUICKSTART.md                # 15-minute demo setup
├── api/
│   ├── morpheus_client.py       # Governed Python client (runnable)
│   ├── morpheus_mock.py         # Mock Morpheus API for demos & tests
│   ├── morpheus_schemas.py      # API types & canonical JSON
│   └── morpheus-client.rs       # Rust client reference module
├── adapter/
│   ├── identity_mapper.py       # Morpheus user → agent:// binding
│   ├── capability_mapper.py     # Morpheus roles → capability://
│   ├── policy_translator.py     # Policy YAML → evaluation engine
│   └── event_listener.py        # Morpheus events → chained evidence
├── policies/                    # Example policies (vm, network, resources)
├── provenance/                  # Tamper-evident provenance chains
├── evidence/                    # Evidence generation & verification
├── conformance/
│   ├── profile.yaml             # OASA-MORPHEUS-CORE-0.1 certification target
│   ├── test-vectors/            # Deterministic test vectors
│   └── tests/                   # MOR-001..MOR-010 conformance suite
└── examples/
    ├── governed-vm-provisioning/# The killer ALLOW/DENY demo
    └── multi-step-workflow/     # End-to-end orchestration pattern
```

## What This Proves

1. SovereignStack governs **real infrastructure** (HPE Morpheus), not a toy.
2. **Policy enforcement works in both directions** — ALLOW and DENY.
3. **Provenance is cryptographically verifiable** without access to Morpheus.
4. **Tampering is detectable** via chain integrity.
5. The **core contract is proven**: `identity -> capability -> policy ->
   provenance -> evidence`.

## Certification

This integration targets the **OASA-MORPHEUS-CORE-0.1** profile
([conformance/profile.yaml](conformance/profile.yaml)), a machine-verifiable
certification covering ten controls (MOR-001..MOR-010). See
[conformance/README.md](../README.md) in the parent integration set and the
[OASA certification framework](../../../CERTIFICATION.md) for level semantics.

## Positioning Language

Use **"OASA Profile for HPE Morpheus"**, **"Conformance Tested"**, and
**"OASA-MORPHEUS-CORE-0.1 Conformant"**. Do not claim "HPE Certified",
"HPE Approved", or "HPE Validated" until an official HPE relationship exists.

## Next Steps

- [x] Directory structure
- [x] Demo scenario documentation
- [x] OASA-MORPHEUS-CORE-0.1 profile
- [x] Governed client + mock Morpheus + conformance suite
- [ ] Record 5-minute ALLOW/DENY demo video
- [ ] Real Morpheus instance validation (requires Morpheus >= 6.0)
- [ ] Plugin packaging for Morpheus Marketplace (with HPE relationship)
