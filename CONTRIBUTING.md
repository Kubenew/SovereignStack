# Contributing to SovereignStack (OASA)

Thank you for your interest in contributing to the **Open Architecture Specification for Autonomous and Sovereign AI**.

## How to Contribute

### Specification Changes

OASA is a standards document. Changes to `OASA.md` require careful review:

1. **Open an Issue** — describe the proposed change and which axiom or layer it affects.
2. **Fork & Branch** — create a feature branch (e.g., `spec/add-secure-federation`).
3. **Update the Spec** — edit `OASA.md` with clear rationale.
4. **Update Schemas** — if the change affects the compliance schema, update the JSON schemas in `schemas/` accordingly.
5. **Validate** — run the compliance validator against your changes:
   ```bash
   pip install -r tools/requirements.txt
   python tools/validate_compliance.py examples/sample_compliance.json
   ```
6. **Submit a PR** — reference the issue and explain the impact.

### Schema Contributions

- Schemas follow **JSON Schema Draft 2020-12**.
- Every field must have a `description`.
- Use `enum` for constrained values.
- Add `examples` where helpful.
- Run syntax validation: `python -m json.tool schemas/your-schema.json`

### Examples

- Examples must work against the OASA-mandated OpenAI-compatible endpoints.
- Shell scripts must pass `bash -n` (syntax check).
- Python scripts must pass `python -m py_compile`.
- Include comments explaining OASA-specific fields (e.g., `oasa_compliance_lock`).

### Tooling

- Tools live in `tools/` with dependencies in `tools/requirements.txt`.
- Keep dependencies minimal.
- Include docstrings and `--help` support.

## Coding Style

- **JSON**: 2-space indent, no trailing commas.
- **Python**: Follow PEP 8. Use type hints. Target Python 3.10+.
- **Shell**: Use `set -euo pipefail`. Quote variables.
- **Markdown**: One sentence per line in specification documents.

## Versioning

The OASA specification uses **calendar versioning** (`YYYY.N`), e.g., `2026.1`.  
Breaking changes increment the minor version and require a deprecation notice.

## Code of Conduct

Be respectful, constructive, and focused on the mission: **keeping AI computation sovereign**.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).
