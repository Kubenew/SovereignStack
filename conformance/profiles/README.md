# Conformance Profiles for SovereignStack Implementations

This directory contains YAML conformance profiles. Each profile defines the
set of tests an implementation must pass to claim a given conformance level.

## Profiles

| Profile | File | Level | Description |
|---------|------|-------|-------------|
| Core Node | `core-node.yaml` | L1 | Minimal kernel services |
| Federation Node | `federation-node.yaml` | L2 | Core + federation |
| Knowledge Node | `knowledge-node.yaml` | L2 | Core + knowledge/reasoning |
| Agent Node | `agent-node.yaml` | L2 | Core + agent execution |

## Usage

```bash
python -m pytest tests/ --profile core-node -v
python tools/generate_report.py --profile knowledge-node --output report.md
```

See RFC-0010 for the full conformance framework specification.
