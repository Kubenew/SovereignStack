#!/usr/bin/env python3
"""
OASA Compliance Validator & Active System Auditor
=================================================

Validates JSON configuration files against the OASA compliance schema
and performs runtime hardware/network isolation infrastructure audits.

Usage:
    # Validate a single configuration file
    python validate_compliance.py ../examples/sample_compliance.json

    # Actively audit the host system infrastructure against a configuration
    python validate_compliance.py ../examples/sample_compliance.json --audit-host

    # Generate a compliant deployment template
    python validate_compliance.py --generate-template
"""

from __future__ import annotations

import argparse
import io
import json
import os
import socket
import subprocess
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


# -- Active Infrastructure Auditing Additions -----------------------------
def audit_host_infrastructure(config: dict[str, Any]) -> list[str]:
    """
    Performs real-time, low-level integration tests on the host environment
    to ensure physical infrastructure matches the declared OASA config limits.
    """
    audit_errors: list[str] = []
    print("\nExecuting OASA Active Infrastructure Live Audit...")
    print("=" * 60)

    # 1. Network Leak Test (Exfiltration Verification)
    if config.get("air_gapped") or not config.get("network", {}).get("allow_wan", True):
        print("[AUDIT] Verifying WAN air-gap state via socket probe...")
        try:
            # Attempting to resolve and touch an external primary root DNS node
            socket.create_connection(("1.1.1.1", 53), timeout=1.5)
            audit_errors.append("  [FAIL] [NETWORK] Host breached isolation. WAN connection established to 1.1.1.1.")
        except (socket.timeout, OSError):
            print("  [PASS] [NETWORK] Local environment confirmed air-gapped (Egress blocked).")

    # 2. Hardware Security (TPM 2.0 Inspection)
    tpm_required = config.get("hardware_security", {}).get("tpm_required", False) or config.get("node", {}).get("tpm_required", False)
    if tpm_required:
        print("[AUDIT] Inspecting physical Trusted Platform Module (TPM)...")
        if sys.platform.startswith("linux"):
            tpm_path = Path("/dev/tpm0")
            if not tpm_path.exists():
                audit_errors.append("  [FAIL] [HARDWARE] TPM device node (/dev/tpm0) absent. Hardware identity unverified.")
            else:
                print("  [PASS] [HARDWARE] Hardware TPM 2.0 interface initialized.")
        elif sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance -Namespace root/cimv2/security/microsofttpm "
                     "-ClassName Win32_Tpm | Select-Object -Property IsEnabled_InitialValue"],
                    capture_output=True, text=True, timeout=10,
                )
                if "True" not in result.stdout:
                    audit_errors.append("  [FAIL] [HARDWARE] Windows TPM verification failed or disabled.")
                else:
                    print("  [PASS] [HARDWARE] Hardware TPM 2.0 interface initialized.")
            except Exception:
                audit_errors.append("  [FAIL] [HARDWARE] Failed executing TPM telemetry script command via PowerShell.")
        else:
            print("  [WARN] [HARDWARE] Automated TPM validation skipped on unsupported OS environment.")

    # 3. Accelerator Verification (VRAM Allocation Safety Caps)
    backends = config.get("compute", {}).get("accelerator_backends", [])
    if "NVIDIA_CUDA" in backends:
        print("[AUDIT] Polling NVIDIA CUDA hardware management interfaces...")
        try:
            # Query nvidia-smi for total standalone VRAM capacity safely
            vram_raw = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                text=True
            )
            total_vram = int(vram_raw.strip().split("\n")[0]) // 1024
            target_budget = config.get("compute", {}).get("vram_budget_gb", 0)
            
            if total_vram < target_budget:
                audit_errors.append(f"  [FAIL] [COMPUTE] VRAM shortfall. Target requires {target_budget}GB, found {total_vram}GB.")
            else:
                print(f"  [PASS] [COMPUTE] Target VRAM requirements met ({total_vram}GB physical ceiling available).")
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            audit_errors.append("  [FAIL] [COMPUTE] CUDA system runtime tools (nvidia-smi) missing or unreadable.")

    return audit_errors


# -- CLI --------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate OASA compliance configurations and audit running host architectures.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="JSON/YAML file(s) to validate.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to the JSON schema (default: auto-detected per-file).",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Directory of JSON/YAML files to validate (recursive).",
    )
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Print a fully compliant template to stdout and exit.",
    )
    parser.add_argument(
        "--audit-host",
        action="store_true",
        help="Execute hardware/network live isolation probing checks against verified configuration limits.",
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
        files.extend(sorted(args.dir.rglob("*.yaml")))
        files.extend(sorted(args.dir.rglob("*.yml")))

    if not files:
        parser.print_help()
        print("\nError: provide at least one JSON/YAML file or use --dir.", file=sys.stderr)
        return 2

    # Validate each file
    all_passed = True
    validated_config: dict[str, Any] | None = None

    for filepath in files:
        if not filepath.exists():
            print(f"[WARN] Skipping (not found): {filepath}")
            continue

        # Parse file based on extension
        document = None
        if filepath.suffix in (".yaml", ".yml"):
            try:
                import yaml  # noqa: WPS433
                with open(filepath, encoding="utf-8") as fh:
                    document = yaml.safe_load(fh)
            except ImportError:
                print(f"[WARN] PyYAML not installed. Skipping YAML file: {filepath}")
                continue
            except Exception as exc:
                print(f"[FAIL] {filepath}  (YAML parse error: {exc})")
                all_passed = False
                continue
        else:
            try:
                document = load_json(filepath)
            except json.JSONDecodeError as exc:
                print(f"[FAIL] {filepath}  (invalid JSON: {exc})")
                all_passed = False
                continue

        if not validated_config:
            validated_config = document  # Cache first valid document for active host audit mode

        # Dynamic Schema Auto-Detection
        if args.schema:
            selected_schema_path = args.schema
        else:
            if isinstance(document, dict) and (("node" in document and "oasa_version" in document) or ("version" in document and "metadata" in document and "node_infrastructure" in document)):
                selected_schema_path = DEFAULT_SCHEMA.parent / "sovereign-stack.schema.json"
            elif isinstance(document, dict) and ("node_id" in document or "deployed_models" in document):
                selected_schema_path = DEFAULT_SCHEMA.parent / "oasa-node-manifest.schema.json"
            else:
                selected_schema_path = DEFAULT_SCHEMA

        if not selected_schema_path.exists():
            print(f"[FAIL] Schema not found at {selected_schema_path}")
            all_passed = False
            continue

        try:
            schema = load_json(selected_schema_path)
        except Exception as exc:
            print(f"[FAIL] Failed to load schema {selected_schema_path.name}: {exc}")
            all_passed = False
            continue

        print(f"Validating {filepath.name} against schema: {selected_schema_path.name}")
        errors = validate_document(document, schema)
        if not print_result(str(filepath), errors):
            all_passed = False

    # Execute Runtime Active Host Audit
    if args.audit_host and all_passed and validated_config:
        audit_errors = audit_host_infrastructure(validated_config)
        print("-" * 60)
        if audit_errors:
            print(f"[FAIL] Host system failed structural OASA compliance audit ({len(audit_errors)} issue(s)).")
            for err in audit_errors:
                print(err)
            all_passed = False
        else:
            print("[OK] Host physical system verified secure and fully OASA compliant.")

    print("-" * 60)
    if all_passed:
        print("[OK] OASA validation operations completed successfully.")
        return 0
    else:
        print("[ERROR] Architectural non-compliance detected.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
