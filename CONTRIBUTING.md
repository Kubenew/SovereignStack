# Contributing to SovereignStack (OASA)

Thank you for your interest in contributing to the **Open Architecture Specification for Autonomous and Sovereign AI**.

## How to Contribute

### Specification Changes

OASA is a standards document. Changes to the specification require careful review:

1. **Open an Issue** — describe the proposed change and which axiom or layer it affects.
2. **Fork & Branch** — create a feature branch (e.g., `spec/add-secure-federation`).
3. **Update the Spec** — edit the relevant document with clear rationale.
4. **RFC Process** — significant changes require an RFC (see [RFC-0000](rfcs/0000-rfc-process.md)).
5. **Update Schemas** — if the change affects the compliance schema, update the JSON schemas in `schemas/` accordingly.
6. **Validate** — run the compliance validator against your changes:
   ```bash
   pip install -r tools/requirements.txt
   python tools/validate_compliance.py examples/sample_compliance.json
   ```
7. **Submit a PR** — reference the issue and explain the impact.

### RFC Process

Major changes follow the RFC lifecycle:

1. **Draft** — Submit a pull request with your RFC document in `rfcs/`
2. **Comment** — Community and TSC review period (minimum 2 weeks)
3. **Refine** — Address feedback and iterate
4. **Accept/Reject** — TSC votes on final proposal
5. **Implement** — Accepted RFCs are tracked in ROADMAP.md

See [RFC-0000](rfcs/0000-rfc-process.md) for complete details.

### RFC Process — Current Priority (v0.5+)

The project prioritizes **implementation maturity and independent reproducibility** of the Core Contract over expansion of the RFC surface.

New RFCs should generally:
- Be required by an active implementation path, or
- Close a clear gap in the Core Contract / conformance model

Speculative or broad architectural RFCs are deferred until the Core Contract verification gate (`bash verify.sh`) remains green and the primary reference adapters are stable.

### Standards Ecosystem

The project now maintains a formal standards framework:

- **[STANDARDS.md](STANDARDS.md)** — Root standards framework with layered architecture
- **[OBJECT_MODEL.md](OBJECT_MODEL.md)** — Universal object model for all entities
- **[URI_STANDARD.md](URI_STANDARD.md)** — URI scheme registry and resolution rules
- **[TRUST_MODEL.md](TRUST_MODEL.md)** — Capability-based security model
- **[SECURITY.md](SECURITY.md)** — Threat model and incident response
- **[CONFORMANCE.md](CONFORMANCE.md)** — Certification program and test suite
- **[CERTIFICATION.md](CERTIFICATION.md)** — Badge levels and requirements
- **[PROTOCOL_REGISTRY.md](PROTOCOL_REGISTRY.md)** — Protocol lifecycle management
- **[REFERENCE_IMPLEMENTATIONS.md](REFERENCE_IMPLEMENTATIONS.md)** — Official implementations

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
