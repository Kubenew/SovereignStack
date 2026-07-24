# SovereignStack Conformance Framework

Automated test suites that verify nodes meet OASA conformance levels. Each level builds on the previous.

## Conformance Levels

| Level | Name | Description | Tests |
|-------|------|-------------|-------|
| **L1** | Compatible | Object model, identity, event bus, URI resolution | `tests/` |
| **L2** | Verified | Capability registry, policy enforcement, federation handshake | `tests/` + L2 markers |
| **L3** | Certified | All mandatory RFCs, SOC 2 mapping, Gaia-X self-description | `tests/` + L3 markers |
| **L4** | Autonomous Intelligence Ready | Meta-cognition, safety contracts, human override, search audit | `level-4-agi/` |

## Running Conformance Tests

```bash
# Run all levels
python -m pytest tests/ -v

# Run only L1
python -m pytest tests/ -v --level L1

# Run L4 (Autonomous Intelligence Ready)
cd conformance/level-4-agi
pytest test_conformance.py -v --sovereign-node=http://localhost:8080

# Generate compliance report
python tools/generate_compliance_report.py --level L4 --output reports/l4-report.md
```

## Test Structure

```
conformance/
├── tests/
│   ├── test_sovereign_objects.py   # L1: Object model conformance
│   ├── rfc/                         # Per-RFC test suites
│   │   ├── test_rfc0001_core_object.py
│   │   ├── test_rfc0002_uri_resolution.py
│   │   └── ...
│   ├── sap/                         # Sovereign Agent Protocol tests
│   ├── sep/                         # Sovereign Event Protocol tests
│   ├── sip/                         # Sovereign Intelligence Protocol tests
│   └── smp/                         # Sovereign Memory Protocol tests
├── level-4-agi/
│   ├── README.md                    # L4 certification spec
│   ├── test_conformance.py          # Full L4 test suite
│   ├── test_metacognition.py        # Meta-cognition tests (RFC-0057)
│   ├── test_safety_contracts.py     # Safety contract tests
│   ├── test_human_override.py       # Kill-switch tests
│   ├── test_search_inference.py     # Search object tests (RFC-0070)
│   └── test_search_execution.py     # Search execution tests (RFC-0071)
├── profiles/                        # Industry-specific conformance profiles
│   ├── finance/
│   ├── government/
│   ├── healthcare/
│   └── manufacturing/
├── fixtures/                        # Test fixtures and mock data
└── certifications/                  # Issued certification records
```

## CI Integration

The conformance suite runs automatically on every push via `.github/workflows/oasa-conformance.yml`:

- **L1**: Always runs
- **L2**: Runs if L1 passes
- **L3**: Runs on main branch only, if L2 passes
- **L4**: Manual trigger or scheduled (weekly)

Badges are generated automatically and committed to gh-pages.

## Creating a Conformance Profile

To add industry-specific conformance tests:

1. Create `conformance/profiles/{industry}/profile.yaml`
2. Define required RFCs and minimum conformance levels
3. Add tests in `conformance/profiles/{industry}/tests/`
4. Reference from `sovereign-stack.yaml` under `conformance.profiles`
