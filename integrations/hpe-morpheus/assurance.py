"""Audit export (MOR-010) — aggregate evidence packages into an audit bundle.

An audit bundle is a single, self-contained JSON report that lets an external
auditor confirm what happened, who acted, which checks ran, and whether the
evidence still verifies — without any access to HPE Morpheus.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable, Optional

from evidence.evidence_verifier import EvidenceVerifier, package_hash


def build_audit_report(
    packages: list,
    public_keys: Optional[Callable[[str], Optional[str]]] = None,
    node_public_key: Optional[str] = None,
) -> dict:
    """Build an audit report from a list of :class:`EvidencePackage` objects.

    When ``public_keys`` and ``node_public_key`` are provided, every package is
    independently re-verified and the result recorded in the report.
    """
    verifier = EvidenceVerifier()
    rows: list[dict] = []
    summary = {"total": 0, "allow": 0, "deny": 0, "escalated": 0, "verified": 0, "unverified": 0}

    for package in packages:
        verified: Optional[bool] = None
        reasons: list[str] = []
        if public_keys is not None and node_public_key is not None:
            verified, reasons = verifier.verify(package, public_keys, node_public_key)
            if verified:
                summary["verified"] += 1
            else:
                summary["unverified"] += 1
        rows.append(
            {
                "package_id": package.package_id,
                "generated_at": package.generated_at,
                "target_object": package.target_object,
                "action": package.action,
                "agent_uri": package.agent_uri,
                "capability": package.capability,
                "decision": package.decision,
                "package_hash": package_hash(package),
                "conformance_profile": package.conformance_profile,
                "verified": verified,
                "verification_reasons": reasons,
                "metadata": package.metadata,
            }
        )
        summary["total"] += 1
        if package.decision == "ALLOW":
            summary["allow"] += 1
        else:
            summary["deny"] += 1
        if package.metadata.get("escalate"):
            summary["escalated"] += 1

    return {
        "report": {
            "name": "sovereignstack-hpe-morpheus-audit",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": "oasa-profile://morpheus-core/v0.1",
        },
        "summary": summary,
        "evidence": rows,
    }


def save_audit(
    path: str,
    packages: list,
    public_keys: Optional[Callable[[str], Optional[str]]] = None,
    node_public_key: Optional[str] = None,
) -> str:
    """Build and persist an audit report to ``path``."""
    report = build_audit_report(packages, public_keys, node_public_key)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return path
