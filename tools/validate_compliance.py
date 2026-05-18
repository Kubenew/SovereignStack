#!/usr/bin/env python3
"""
OASA Compliance Validator
=========================

Validates JSON configuration files against the OASA compliance schema.
Use this to audit Sovereign Node configurations before deployment.

Usage:
    # Validate a single file
    python validate_compliance.py ../examples/sample_compliance.json

    # Validate with a specific schema
    python validate_compliance.py config.json --schema ../schemas/oasa-compliance.schema.json

    # Validate all JSON files in a directory
    python validate_compliance.py --dir /etc/oasa/configs/

    # Generate a compliant template
    python validate_compliance.py --generate-template
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Any

# Fix Windows console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print(
        "ERROR: 'jsonschema' package is required.\n"
        "Install it with:  pip install jsonschema\n"
        "Or:               pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)


# -- Paths -----------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEMA = SCRIPT_DIR.parent / "schemas" / "oasa-compliance.schema.json"


# -- Template --------------------------------------------------------------
COMPLIANT_TEMPLATE: dict[str, Any] = {
    "oasa_version": "2026.1",
    "enforce_zero_exfiltration": True,
    "oasa_compliance_lock": True,
    "compliance_level": "STRICT",
    "air_gapped": True,
    "network": {
        "allow_wan": False,
        "allowed_egress_cidrs": [],
        "dns_mode": "LOCAL_ONLY",
    },
    "encryption": {
        "algorithm": "AES-256-GCM",
        "key_management": "TPM_2.0",
        "key_rotation_days": 90,
    },
    "hardware_security": {
        "tpm_required": True,
        "tpm_version": "2.0",
        "hsm_type": None,
        "secure_boot": True,
    },
    "compute": {
        "vram_budget_gb": 24,
        "quantization_formats": ["FP16", "INT4", "AWQ"],
        "accelerator_backends": ["NVIDIA_CUDA"],
    },
    "ingestion": {
        "allow_disk_cache": False,
        "supported_formats": ["PDF", "TIFF", "DOCX", "HTML"],
    },
    "audit": {
        "enabled": True,
        "log_format": "JSON",
        "immutable": True,
        "retention_days": 365,
    },
    "api": {
        "openai_compatible": True,
        "base_url": "http://localhost:8080/v1",
        "endpoints": ["/v1/chat/completions", "/v1/embeddings"],
    },
}


# -- Helpers ----------------------------------------------------------------
def load_json(path: Path) -> Any:
    """Load and parse a JSON file."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_document(
    document: dict[str, Any],
    schema: dict[str, Any],
    source: str = "<stdin>",
) -> list[str]:
    """Validate *document* against *schema*. Returns a list of error strings."""
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  [FAIL] [{path}] {error.message}")
    return errors


def print_result(source: str, errors: list[str]) -> bool:
    """Print validation results. Returns True if valid."""
    if errors:
        print(f"\n[FAIL] {source}  ({len(errors)} violation(s))")
        for err in errors:
            print(err)
        return False
    else:
        print(f"[PASS] {source}")
        return True


# -- CLI --------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate OASA compliance configurations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="JSON file(s) to validate.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Path to the JSON schema (default: {DEFAULT_SCHEMA.name}).",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Directory of JSON files to validate (recursive).",
    )
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Print a fully compliant template to stdout and exit.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Template generation mode
    if args.generate_template:
        print(json.dumps(COMPLIANT_TEMPLATE, indent=2))
        return 0

    # Collect input files
    files: list[Path] = list(args.files or [])
    if args.dir:
        files.extend(sorted(args.dir.rglob("*.json")))

    if not files:
        parser.print_help()
        print("\nError: provide at least one JSON file or use --dir.", file=sys.stderr)
        return 2

    # Load schema
    if not args.schema.exists():
        print(f"Error: schema not found at {args.schema}", file=sys.stderr)
        return 2

    schema = load_json(args.schema)
    print(f"Schema: {args.schema.name}  (OASA {schema.get('title', 'unknown')})")
    print("-" * 60)

    # Validate each file
    all_passed = True
    for filepath in files:
        if not filepath.exists():
            print(f"[WARN] Skipping (not found): {filepath}")
            continue
        try:
            document = load_json(filepath)
        except json.JSONDecodeError as exc:
            print(f"[FAIL] {filepath}  (invalid JSON: {exc})")
            all_passed = False
            continue

        errors = validate_document(document, schema, source=str(filepath))
        if not print_result(str(filepath), errors):
            all_passed = False

    print("-" * 60)
    if all_passed:
        print("[OK] All files passed OASA compliance validation.")
        return 0
    else:
        print("[ERROR] Some files failed validation. See errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
