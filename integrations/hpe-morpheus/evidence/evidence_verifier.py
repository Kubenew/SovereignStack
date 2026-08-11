"""Independent verification of Morpheus evidence packages.

The verifier needs only the package and the relevant public keys. It never
contacts HPE Morpheus, so a third party (auditor, regulator, CISO) can confirm
that a governed operation really happened, was authorized, and was not tampered
with.
"""

from __future__ import annotations

from typing import Callable, Optional

from crypto import hash_bytes, verify
from evidence.evidence_generator import EvidencePackage
from provenance.morpheus_provenance_chain import ProvenanceChain


class EvidenceVerifier:
    """Verifies linkage, content hashes, signatures, and package signature."""

    def verify(
        self,
        package: EvidencePackage,
        public_keys: Callable[[str], Optional[str]],
        node_public_key: Optional[str] = None,
    ) -> tuple[bool, list[str]]:
        """Return ``(valid, reasons)``.

        ``public_keys`` resolves an agent URI to its public key hex; package
        signatures are verified against ``node_public_key``.
        """
        reasons: list[str] = []

        if not package.signature:
            reasons.append("package is unsigned")
            return False, reasons
        if node_public_key is None:
            reasons.append("node public key not provided")
            return False, reasons
        if not verify(package.canonical_bytes(), package.signature, node_public_key):
            reasons.append("package signature invalid")
            return False, reasons

        chain = ProvenanceChain.from_dict(package.chain)
        valid, chain_reasons = chain.verify(public_keys, node_public_key)
        reasons.extend(chain_reasons)
        if not valid:
            return False, reasons

        reasons.append(
            f"evidence verified: decision={package.decision} "
            f"action={package.action} profile={package.conformance_profile}"
        )
        return True, reasons

    def verify_dict(
        self,
        package_dict: dict,
        registry: dict,
        node_public_key: str,
    ) -> tuple[bool, list[str]]:
        """Convenience wrapper over a plain ``{agent_uri: public_key_hex}`` dict."""

        def _resolve(agent_uri: str) -> Optional[str]:
            return registry.get(agent_uri)

        return self.verify(
            EvidencePackage.from_dict(package_dict), _resolve, node_public_key
        )


def package_hash(package: EvidencePackage) -> str:
    """Stable content hash of a package, useful for audit indexes."""
    return hash_bytes(package.canonical_bytes())
