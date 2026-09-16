"""
OASA Action Envelope and Server-Side Atomic Authorization Engine
Specification: OASA v0.6 Governed Autonomous Action
"""

import json
import hashlib
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature


def _reject_unsupported(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(f"deterministic-json-v1 requires string keys, got: {type(k)}")
            _reject_unsupported(v)
    elif isinstance(obj, list):
        for item in obj:
            _reject_unsupported(item)
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        raise TypeError(f"deterministic-json-v1 rejects unsupported type: {type(obj)}")

def canonical_json_bytes(obj: Any) -> bytes:
    """
    Serialize Python dictionary to `deterministic-json-v1` bytes.
    - UTF-8 encoding
    - JSON object keys sorted lexicographically
    - No insignificant whitespace
    - Unsupported values rejected (not a full RFC 8785 implementation)
    """
    _reject_unsupported(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Compute standard SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


class TokenStateStore:
    """
    Server-side thread-safe atomic state store for authorization tokens.
    Guarantees single-use token consumption via atomic test-and-set.
    Eliminates race conditions and replay attacks.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # token_id -> { "issued_at": datetime, "expires_at": datetime, "consumed_at": Optional[datetime], "metadata": dict }
        self._tokens: Dict[str, Dict[str, Any]] = {}

    def issue_token(self, token_id: str, actor_id: str, action: str, target_uri: str, ttl_seconds: int = 300) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc)
            record = {
                "token_id": token_id,
                "actor_id": actor_id,
                "action": action,
                "target_uri": target_uri,
                "issued_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
                "consumed_at": None,
            }
            self._tokens[token_id] = record
            return record

    def consume_token(self, token_id: str, presenting_actor_id: str, target_uri: str) -> Tuple[bool, str]:
        """
        Atomically checks validity and consumes the token in one operation.
        Returns (success: bool, reason: str).
        """
        with self._lock:
            if token_id not in self._tokens:
                return False, "TOKEN_NOT_FOUND"

            record = self._tokens[token_id]

            if record["consumed_at"] is not None:
                return False, "TOKEN_ALREADY_CONSUMED"

            # Check expiration
            expires_at = datetime.fromisoformat(record["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                return False, "TOKEN_EXPIRED"

            # Check actor identity
            if record["actor_id"] != presenting_actor_id:
                return False, "ACTOR_MISMATCH"

            # Check target immutability
            if record["target_uri"] != target_uri:
                return False, "TARGET_MISMATCH"

            # Atomically mark consumed
            record["consumed_at"] = datetime.now(timezone.utc).isoformat()
            return True, "TOKEN_CONSUMED"

    def is_consumed(self, token_id: str) -> bool:
        with self._lock:
            if token_id in self._tokens:
                return self._tokens[token_id]["consumed_at"] is not None
            return False


class EnvelopeSigner:
    """
    Cryptographic authority for signing and verifying Action Envelopes using Ed25519.
    """

    def __init__(self, private_key: Optional[ed25519.Ed25519PrivateKey] = None):
        if private_key is None:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            self._private_key = private_key
        self._public_key = self._private_key.public_key()

    @property
    def public_key_hex(self) -> str:
        raw_bytes = self._public_key.public_bytes_raw()
        return raw_bytes.hex()

    def sign_payload(self, payload: Dict[str, Any]) -> str:
        """Sign canonical JSON digest with Ed25519 private key."""
        canonical_bytes = canonical_json_bytes(payload)
        sig_bytes = self._private_key.sign(canonical_bytes)
        return sig_bytes.hex()

    @staticmethod
    def verify_signature(payload: Dict[str, Any], signature_hex: str, public_key_hex: str) -> bool:
        """Strict cryptographic verification of signature against canonical payload and public key."""
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
            sig_bytes = bytes.fromhex(signature_hex)
            canonical_bytes = canonical_json_bytes(payload)
            public_key.verify(sig_bytes, canonical_bytes)
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False


class ActionEnvelopeBuilder:
    """
    Builder and verifier for OASA Action Envelopes.
    """

    @staticmethod
    def create_envelope(
        action_id: str,
        actor_id: str,
        actor_type: str,
        capability_id: str,
        target_uri: str,
        decision: str,
        token_id: Optional[str] = None,
        delegation: Optional[List[Dict[str, Any]]] = None,
        policy_id: Optional[str] = None,
        provider: Optional[str] = None,
        provider_action_id: Optional[str] = None,
        request_payload: Optional[Dict[str, Any]] = None,
        provider_audit_payload: Optional[Dict[str, Any]] = None,
        signer: Optional[EnvelopeSigner] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()

        req_bytes = canonical_json_bytes(request_payload or {})
        req_hash = sha256_hex(req_bytes)

        auth_data = {
            "decision": decision,
            "token_id": token_id,
            "reason": reason or ("Allowed by policy" if decision == "allow" else "Denied by policy"),
        }
        auth_hash = sha256_hex(canonical_json_bytes(auth_data))

        exec_hash = None
        if provider_action_id:
            exec_hash = sha256_hex(canonical_json_bytes({"provider": provider, "provider_action_id": provider_action_id}))

        audit_hash = None
        if provider_audit_payload:
            audit_hash = sha256_hex(canonical_json_bytes(provider_audit_payload))

        hashes = {
            "request": req_hash,
            "authorization": auth_hash,
        }
        if exec_hash:
            hashes["execution"] = exec_hash
        if audit_hash:
            hashes["provider_audit"] = audit_hash

        envelope: Dict[str, Any] = {
            "oasa_version": "0.6",
            "envelope_version": "0.1",
            "action_id": action_id,
            "actor": {
                "id": actor_id,
                "type": actor_type,
            },
            "delegation": delegation or [],
            "capability": {
                "id": capability_id,
            },
            "target": {
                "uri": target_uri,
            },
            "policy": {
                "id": policy_id or "default-policy",
            },
            "authorization": auth_data,
            "evidence": {
                "hashes": hashes,
            },
            "provenance": {
                "timestamp": now_iso,
            },
        }

        if provider and provider_action_id:
            envelope["execution"] = {
                "provider": provider,
                "provider_action_id": provider_action_id,
                "executed_at": now_iso,
                "status": "SUCCESS",
            }

        # Cryptographic signing
        if signer:
            # We sign the body of the envelope without the signature itself
            payload_to_sign = {k: v for k, v in envelope.items() if k != "evidence"}
            payload_to_sign["evidence_hashes"] = hashes
            sig = signer.sign_payload(payload_to_sign)
            envelope["evidence"]["signature"] = sig
            envelope["evidence"]["signer_public_key"] = signer.public_key_hex

        return envelope

    @staticmethod
    def verify_envelope(
        envelope: Dict[str, Any],
        request_payload: Optional[Dict[str, Any]] = None,
        provider_audit_payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Independently verifies all cryptographic links and signatures on an Action Envelope.
        """
        results: Dict[str, str] = {}

        evidence = envelope.get("evidence", {})
        hashes = evidence.get("hashes", {})
        sig = evidence.get("signature")
        pubkey = evidence.get("signer_public_key")

        # 1. Structural checks
        if not envelope.get("action_id") or not envelope.get("actor") or not envelope.get("target"):
            results["structure"] = "FAIL: Missing required envelope fields"
            return False, results
        results["structure"] = "PASS"

        # 2. Signature verification
        if not sig or not pubkey:
            results["signature"] = "FAIL: Missing signature or public key"
            return False, results

        payload_to_verify = {k: v for k, v in envelope.items() if k != "evidence"}
        payload_to_verify["evidence_hashes"] = hashes

        is_valid = EnvelopeSigner.verify_signature(payload_to_verify, sig, pubkey)
        if not is_valid:
            results["signature"] = "FAIL: Signature mismatch"
            return False, results
        results["signature"] = "PASS"

        # 3. Hash integrity
        if "request" not in hashes or not hashes["request"]:
            results["hashes"] = "FAIL: Missing request hash"
            return False, results

        if request_payload is not None:
            expected_req_hash = sha256_hex(canonical_json_bytes(request_payload))
            if hashes["request"] != expected_req_hash:
                results["hashes"] = "FAIL: Request hash mismatch"
                return False, results

        if "authorization" in hashes and "authorization" in envelope:
            expected_auth_hash = sha256_hex(canonical_json_bytes(envelope["authorization"]))
            if hashes["authorization"] != expected_auth_hash:
                results["hashes"] = "FAIL: Authorization hash mismatch"
                return False, results

        if "execution" in hashes and "execution" in envelope:
            expected_exec_hash = sha256_hex(canonical_json_bytes({
                "provider": envelope["execution"].get("provider"),
                "provider_action_id": envelope["execution"].get("provider_action_id")
            }))
            if hashes["execution"] != expected_exec_hash:
                results["hashes"] = "FAIL: Execution hash mismatch"
                return False, results

        if "provider_audit" in hashes and provider_audit_payload is not None:
            expected_audit_hash = sha256_hex(canonical_json_bytes(provider_audit_payload))
            if hashes["provider_audit"] != expected_audit_hash:
                results["hashes"] = "FAIL: Provider audit hash mismatch"
                return False, results

        results["hashes"] = "PASS"

        # 4. Provider action ID linkage and Evidence (EVID-003)
        auth = envelope.get("authorization", {})
        exec_block = envelope.get("execution", {})
        
        if auth.get("decision") == "allow" and exec_block.get("status") == "SUCCESS":
            prov_action_id = exec_block.get("provider_action_id")
            if not prov_action_id:
                results["provider_linkage"] = "FAIL: Missing provider_action_id for successful action"
                return False, results
            
            if "provider_audit" not in hashes:
                results["provider_linkage"] = "FAIL: Missing provider_audit evidence for successful action"
                return False, results
                
            if provider_audit_payload is not None:
                if provider_audit_payload.get("provider_action_id") != prov_action_id:
                    results["provider_linkage"] = "FAIL: Provider audit payload does not bind to provider_action_id"
                    return False, results

            results["provider_linkage"] = "PASS"
        elif auth.get("decision") == "allow":
            # If not SUCCESS, we might not have a provider action ID, but if we do, it shouldn't fail EVID-003.
            # We'll just mark PASS if it's allowed but failed execution (e.g. LIVE_EXECUTION_NOT_CONFIGURED)
            results["provider_linkage"] = "PASS"
        else:
            # Denied actions
            results["provider_linkage"] = "PASS"

        return True, results
