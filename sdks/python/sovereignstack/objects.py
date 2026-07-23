"""SovereignStack object model — Python dataclasses for all URI scheme types."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SovereignObject:
    """Base class for all SovereignStack objects."""
    uri: str
    kind: str
    data: dict[str, Any]
    created_at: str = field(default_factory=_timestamp)
    signature: str = ""

    def sign(self, signer: str) -> "SovereignObject":
        payload = json.dumps({"uri": self.uri, "data": self.data}, sort_keys=True).encode()
        self.signature = f"ed25519:{_sha256_hex(payload)[:16]}:{signer}"
        return self

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "kind": self.kind,
            "data": self.data,
            "created_at": self.created_at,
            "signature": self.signature,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "SovereignObject":
        d = json.loads(raw)
        return cls(uri=d["uri"], kind=d["kind"], data=d["data"],
                   created_at=d.get("created_at", ""), signature=d.get("signature", ""))


@dataclass
class Payment(SovereignObject):
    """Payment instruction (ISO 20022 pacs.008 compatible)."""
    kind: str = "payment"

    @classmethod
    def create(cls, uri: str, sender: str, receiver: str, amount: float,
               currency: str, originator: str = "", beneficiary: str = "",
               compliance_ref: str = "") -> "Payment":
        return cls(
            uri=uri,
            data={
                "type": "pacs.008",
                "sender": sender,
                "receiver": receiver,
                "amount": {"value": amount, "currency": currency},
                "originator": originator,
                "beneficiary": beneficiary,
                "status": "initiated",
                "compliance_ref": compliance_ref,
            },
        )


@dataclass
class Settlement(SovereignObject):
    """Settlement record — delivery vs payment."""
    kind: str = "settlement"

    @classmethod
    def create(cls, uri: str, payment_ref: str, method: str,
               asset: str, amount: dict, status: str = "pending") -> "Settlement":
        return cls(
            uri=uri,
            data={
                "payment_ref": payment_ref,
                "method": method,
                "asset": asset,
                "amount": amount,
                "status": status,
                "settled_at": _timestamp(),
            },
        )


@dataclass
class Treasury(SovereignObject):
    """Treasury instruction — credit/debit on a treasury account."""
    kind: str = "treasury"

    @classmethod
    def create(cls, uri: str, treasury_account: str, action: str,
               amount: dict, approved_by: str = "") -> "Treasury":
        return cls(
            uri=uri,
            data={
                "treasury_account": treasury_account,
                "action": action,
                "amount": amount,
                "approved_by": approved_by,
                "status": "executed",
            },
        )


@dataclass
class PolicyEvaluation(SovereignObject):
    """Policy engine evaluation result."""
    kind: str = "policy_evaluation"

    @classmethod
    def create(cls, uri: str, payment_ref: str, checks: dict,
               overall_result: str, score: float, evaluator: str) -> "PolicyEvaluation":
        return cls(
            uri=uri,
            data={
                "payment_ref": payment_ref,
                "checks": checks,
                "overall_result": overall_result,
                "score": score,
                "evaluator": evaluator,
                "timestamp": _timestamp(),
            },
        )


@dataclass
class AuditRecord(SovereignObject):
    """Audit record — hashed chain of all transaction objects."""
    kind: str = "audit_record"

    @classmethod
    def create(cls, uri: str, chain: list[str], total_amount: dict,
               auditor: str) -> "AuditRecord":
        chain_hash = _sha256_hex(json.dumps(chain).encode())
        return cls(
            uri=uri,
            data={
                "transaction_chain": chain,
                "chain_hash": chain_hash,
                "total_amount": total_amount,
                "audit_timestamp": _timestamp(),
                "auditor": auditor,
            },
        )


@dataclass
class ProvenanceLog(SovereignObject):
    """Provenance graph entry — immutable log of all objects."""
    kind: str = "provenance_log"

    @classmethod
    def create(cls, uri: str, objects: list[SovereignObject],
               signer: str) -> "ProvenanceLog":
        entries = [
            {"uri": o.uri, "kind": o.kind, "signature": o.signature, "created_at": o.created_at}
            for o in objects
        ]
        return cls(
            uri=uri,
            data={
                "entries": entries,
                "total_entries": len(entries),
                "root_hash": _sha256_hex(json.dumps(entries).encode()),
            },
        ).sign(signer)
