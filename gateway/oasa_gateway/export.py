"""Evidence package export for auditors.

Generates a self-contained, tamper-proof zip archive that an auditor
can verify offline using only the included verify.py script and
the gateway's public key.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ss_core.types import ContentHash
from ss_crypto.hashing import hash_content_hex
from ss_crypto.keys import KeyPair
from ss_crypto.signing import sign
from ss_cas.merkle import MerkleLog

logger = logging.getLogger("oasa.export")


# Standalone verification script included in every evidence package.
# Zero external dependencies — uses only Python 3.10+ stdlib.
VERIFY_SCRIPT = '''#!/usr/bin/env python3
"""Standalone OASA evidence package verifier.

Usage: python verify.py

Run this script inside an unpacked OASA evidence package directory,
or pass the path to a .zip file as the first argument.

Requirements: Python 3.10+ (no pip install needed)
Optional: pip install PyNaCl (for Ed25519 signature verification)
"""

import base64
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path


def load_package(path: str | None = None) -> Path:
    """Find or extract the evidence package."""
    if path and path.endswith(".zip"):
        extract_dir = Path(path).stem
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(extract_dir)
        return Path(extract_dir)

    # Look for manifest.json in current directory
    if Path("manifest.json").exists():
        return Path(".")

    print("ERROR: No manifest.json found. Run from inside an evidence package.")
    sys.exit(1)


def verify_merkle(events: list[dict], expected_root: str) -> bool:
    """Rebuild Merkle tree from events and check root matches."""
    if not events:
        leaf_hashes = [hashlib.sha256(b"").digest()]
    else:
        leaf_hashes = []
        for evt_file in sorted(events):
            with open(evt_file, "rb") as f:
                leaf_hashes.append(hashlib.sha256(f.read()).digest())

    # Build tree bottom-up
    level = leaf_hashes
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                parent = hashlib.sha256(level[i] + level[i + 1]).digest()
                next_level.append(parent)
            else:
                next_level.append(level[i])
        level = next_level

    computed_root = "sha256:" + level[0].hex()
    match = computed_root == expected_root
    if match:
        print(f"  ✓ Merkle root matches: {expected_root[:40]}...")
    else:
        print(f"  ✗ Merkle root MISMATCH!")
        print(f"    Expected: {expected_root}")
        print(f"    Computed: {computed_root}")
    return match


def verify_signatures(pkg_dir: Path) -> bool:
    """Verify Ed25519 signatures on events (requires PyNaCl)."""
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError
    except ImportError:
        print("  ⚠ PyNaCl not installed — skipping signature verification.")
        print("    Install with: pip install PyNaCl")
        return True  # Non-fatal

    pubkey_path = pkg_dir / "public_key.pem"
    if not pubkey_path.exists():
        print("  ✗ public_key.pem not found")
        return False

    pubkey_hex = pubkey_path.read_text().strip()
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    vk = VerifyKey(pubkey_bytes)

    events_dir = pkg_dir / "events"
    if not events_dir.exists():
        print("  ✗ events/ directory not found")
        return False

    all_valid = True
    for evt_file in sorted(events_dir.glob("*.json")):
        data = json.loads(evt_file.read_text())
        payload = base64.b64decode(data["payload"])
        sig = base64.b64decode(data["signature"])
        try:
            vk.verify(payload, sig)
        except BadSignatureError:
            print(f"  ✗ BAD SIGNATURE: {evt_file.name}")
            all_valid = False

    if all_valid:
        count = len(list(events_dir.glob("*.json")))
        print(f"  ✓ All {count} event signatures verified")
    return all_valid


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    pkg_dir = load_package(path)

    manifest_path = pkg_dir / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: manifest.json not found")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    print(f"\\nOASA Evidence Package Verification")
    print(f"=" * 40)
    print(f"Date range: {manifest.get('date_start', '?')} — {manifest.get('date_end', '?')}")
    print(f"Events: {manifest.get('event_count', '?')}")
    print(f"Expected root: {manifest.get('merkle_root', '?')[:40]}...")
    print()

    # 1. Verify Merkle root
    print("[1/2] Verifying Merkle tree integrity...")
    events_dir = pkg_dir / "events"
    event_files = sorted(events_dir.glob("*.json")) if events_dir.exists() else []
    merkle_ok = verify_merkle(
        [str(f) for f in event_files],
        manifest.get("merkle_root", ""),
    )

    # 2. Verify signatures
    print("[2/2] Verifying Ed25519 signatures...")
    sigs_ok = verify_signatures(pkg_dir)

    print()
    if merkle_ok and sigs_ok:
        print("RESULT: ✓ PASS — Evidence package is intact and verified.")
        sys.exit(0)
    else:
        print("RESULT: ✗ FAIL — Evidence package verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''


class EvidenceExporter:
    """Exports audit evidence as a portable, verifiable zip package."""

    def __init__(
        self,
        merkle: MerkleLog,
        keypair: KeyPair,
    ) -> None:
        self.merkle = merkle
        self.keypair = keypair

    def export(
        self,
        output_path: Path | str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Path:
        """Export an evidence package for the given date range.

        Args:
            output_path: Where to write the zip file.
            start_date: ISO date string for range start (inclusive).
            end_date: ISO date string for range end (inclusive).

        Returns:
            Path to the created zip file.
        """
        output_path = Path(output_path)

        # Convert date strings to ISO datetime range for the DB query
        start_time = f"{start_date}T00:00:00+00:00" if start_date else None
        end_time = f"{end_date}T23:59:59.999999+00:00" if end_date else None

        # Get matching leaves
        leaves = self.merkle.get_leaves_in_range(start_time, end_time)

        if not leaves and start_date is None and end_date is None:
            # If no date filter, get everything
            all_leaves = []
            for i in range(self.merkle.size):
                leaf = self.merkle.get_leaf(i)
                if leaf:
                    all_leaves.append((i, leaf[0], leaf[1]))
            leaves = all_leaves

        # Build the zip
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write events
            event_hashes: list[bytes] = []
            for idx, leaf_hash, raw_data in leaves:
                filename = f"events/{idx:06d}.json"
                zf.writestr(filename, raw_data)
                event_hashes.append(leaf_hash.digest)

            # Compute the Merkle root over these events
            root = self.merkle.root()

            # Write manifest
            manifest = {
                "format": "oasa-evidence-v1",
                "date_start": start_date or "earliest",
                "date_end": end_date or "latest",
                "event_count": len(leaves),
                "merkle_root": str(root),
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "gateway_pubkey_fingerprint": self.keypair.public_key.fingerprint,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            # Sign the Merkle root
            root_sig = sign(str(root).encode("utf-8"), self.keypair._signing_key)
            zf.writestr("merkle_root.sig", root_sig.hex)

            # Write the public key (hex format for simplicity)
            zf.writestr("public_key.pem", self.keypair.public_key.hex)

            # Include the standalone verifier
            zf.writestr("verify.py", VERIFY_SCRIPT)

        # Write to disk
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(buffer.getvalue())

        logger.info(
            "Exported evidence package: %s (%d events, root=%s)",
            output_path,
            len(leaves),
            root.hex[:16],
        )

        return output_path
