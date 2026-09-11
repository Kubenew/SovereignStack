# Conformance Profiles for SovereignStack Implementations

This directory contains YAML conformance profiles. Each profile defines the
set of tests an implementation must pass to claim a given conformance level.

## Profiles

| Profile | File | Level | Description |
|---------|------|-------|-------------|
| Core 0.1 (**Authoritative**) | `profiles/core/0.1.yaml` | L1 | Authoritative OASA Core Contract & Governed Autonomous Action |
| Federation Node | `conformance/profiles/federation-node.yaml` | L2 | Core + federation |
| Knowledge Node | `conformance/profiles/knowledge-node.yaml` | L2 | Core + knowledge/reasoning |
| Agent Node | `conformance/profiles/agent-node.yaml` | L2 | Core + agent execution |

## Usage

```bash
python -m pytest tests/ --profile core-0.1 -v
python tools/generate_report.py --profile knowledge-node --output report.md
```

See RFC-0010 for the full conformance framework specification.
