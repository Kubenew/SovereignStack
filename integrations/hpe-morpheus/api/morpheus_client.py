"""Governed Morpheus client.

Orchestrates the full SovereignStack core contract for one action:

    identity -> capability -> policy -> decision -> (Morpheus) -> provenance -> evidence

Morpheus is only contacted when the governing decision is ALLOW. Denials are
recorded as evidence too, so both paths are auditable.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
import uuid

from adapter.capability_mapper import CapabilityMapper
from adapter.identity_mapper import IdentityMapper
from adapter.policy_translator import PolicyEvaluator
from api.morpheus_schemas import GovernedDecision, GovernedRequest, canonical_json
from crypto import sign
from evidence.evidence_generator import EvidencePackage
from provenance.morpheus_provenance_chain import ProvenanceChain, ProvenanceEntry

CONFORMANCE_PROFILE = "oasa-profile://morpheus-core/v0.1"


class GovernanceError(Exception):
    pass


class GovernedClient:
    def __init__(
        self,
        endpoint: str,
        identity: IdentityMapper,
        capabilities: CapabilityMapper,
        policies: PolicyEvaluator,
        chain: ProvenanceChain,
        node_private_key_hex: str,
        node_public_key_hex: str,
        timeout: float = 5.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.identity = identity
        self.capabilities = capabilities
        self.policies = policies
        self.chain = chain
        self.node_private_key_hex = node_private_key_hex
        self.node_public_key_hex = node_public_key_hex
        self.timeout = timeout
        self._seen_nonces: set = set()
        self._packages: list = []
        self._bearer_token: str | None = None

    def authenticate(self, username: str, password: str) -> str:
        """Authenticate against Morpheus and cache the bearer token.

        Maps the authenticated user onto its bound agent identity
        (``identity.resolve_agent``) and returns the token.
        """
        url = f"{self.endpoint}/api/auth/token"
        body = json.dumps({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise GovernanceError(f"Morpheus auth returned {exc.code}: {exc.read().decode()}")
        token = payload.get("accessToken")
        if not token:
            raise GovernanceError("Morpheus auth response missing accessToken")
        self._bearer_token = token
        return token

    # ── governance pipeline ──────────────────────────────────────────────

    def govern(self, request: GovernedRequest, quota: dict | None = None) -> GovernedDecision:
        checks: list[dict] = []
        decision = GovernedDecision(
            decision="DENY", agent_uri=request.agent_uri, capability=request.capability
        )

        # Replay protection
        if request.nonce in self._seen_nonces:
            decision.reason = "REPLAY_DETECTED"
            decision.checks = [{"check": "nonce", "result": "FAIL", "detail": "nonce reused"}]
            self._record(request, decision, detail={"reason": decision.reason})
            return decision
        self._seen_nonces.add(request.nonce)

        # 1. Identity
        ok, reason = self.identity.verify_request(
            request.agent_uri, request.message(), request.signature or ""
        )
        checks.append({"check": "identity", "result": "PASS" if ok else "FAIL", "detail": reason})
        if not ok:
            decision.reason = "IDENTITY_VIOLATION"
            decision.checks = checks
            self._record(request, decision, detail={"reason": decision.reason, "checks": checks})
            return decision

        # 2. Capability
        allowed, reason = self.capabilities.authorize(request.agent_uri, request.capability)
        checks.append(
            {"check": "capability", "result": "PASS" if allowed else "FAIL", "detail": reason}
        )
        if not allowed:
            decision.reason = "CAPABILITY_VIOLATION"
            decision.checks = checks
            self._record(request, decision, detail={"reason": decision.reason, "checks": checks})
            return decision

        # 3. Policy (RFC-0075 safe-halt on conflict)
        allow, reasons, violations, escalate = self.policies.evaluate(request.spec, quota)
        checks.append(
            {
                "check": "policy",
                "result": "ALLOW" if allow else "DENY",
                "detail": "; ".join(reasons),
                "violations": violations,
                "escalate": escalate,
            }
        )
        if not allow:
            decision.reason = "POLICY_VIOLATION" if not escalate else "POLICY_CONFLICT_ESCALATED"
            decision.escalate = escalate
            decision.checks = checks
            self._record(request, decision, detail={"reason": decision.reason, "violations": violations})
            return decision

        # 4. Execute against Morpheus (governed call)
        vm_id = self._call_morpheus(request.spec)
        decision.decision = "ALLOW"
        decision.morpheus_called = True
        decision.vm_id = vm_id
        decision.checks = checks
        self._record(
            request,
            decision,
            detail={"vm_id": vm_id, "checks": checks},
        )
        return decision

    # ── internals ────────────────────────────────────────────────────────

    def _call_morpheus(self, spec: dict) -> str:
        url = f"{self.endpoint}/api/vms"
        body = json.dumps(spec).encode("utf-8")
        token = self._bearer_token or "mock-token"
        req = urllib.request.Request(
            url, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise GovernanceError(f"Morpheus returned {exc.code}: {exc.read().decode()}")
        if "id" not in payload:
            raise GovernanceError("Morpheus response missing vm id")
        return payload["id"]

    def _record(
        self,
        request: GovernedRequest,
        decision: GovernedDecision,
        detail: dict,
    ) -> None:
        """Append a signed provenance entry and build an evidence package."""
        object_uri = f"vm://morpheus/{decision.vm_id}" if decision.vm_id else \
            f"denied://morpheus/{request.action}/{request.nonce}"
        prev_hash = self.chain.entries[-1].hash() if self.chain.entries else None
        entry = ProvenanceEntry(
            seq=len(self.chain.entries) + 1,
            action=request.action,
            agent_uri=request.agent_uri,
            object_uri=object_uri,
            decision=decision.decision,
            detail=detail,
            prev_hash=prev_hash,
            nonce=request.nonce,
        )
        self.chain.append(entry, private_key_hex=self.node_private_key_hex)

        package = EvidencePackage.new(
            generated_by="node://morpheus-gateway",
            conformance_profile=CONFORMANCE_PROFILE,
            target_object=object_uri,
            action=request.action,
            agent_uri=request.agent_uri,
            capability=request.capability,
            decision=decision.decision,
            checks=decision.checks,
            chain=self.chain,
            metadata={"reason": decision.reason, "morpheus_called": decision.morpheus_called, "escalate": decision.escalate},
        ).sign(self.node_private_key_hex)

        decision.evidence_uri = f"evidence://morpheus/{request.action}/{request.nonce[:8]}"
        decision.chain_uri = f"chain://morpheus/{request.agent_uri.split('://')[1]}"
        self._last_package = package
        self._packages.append(package)

    @property
    def last_package(self) -> EvidencePackage:
        return self._last_package


def demo_agent() -> tuple[str, str]:
    """Create a fresh demo agent keypair."""
    from crypto import generate_keypair

    return generate_keypair()


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed HPE Morpheus client")
    parser.add_argument("--endpoint", default="http://localhost:8548")
    parser.add_argument("--action", default="provision-vm")
    parser.add_argument("--agent", default="agent://ml-platform")
    parser.add_argument("--capability", default="capability://compute/provision")
    parser.add_argument("--spec", required=False, help="JSON request spec (inline)")
    parser.add_argument("--spec-file", required=False, help="Path to a JSON spec or request envelope")
    parser.add_argument("--quota", required=False, help="Tenant quota context (JSON)")
    parser.add_argument("--username", default=None, help="Morpheus user (optional)")
    parser.add_argument("--password", default=None, help="Morpheus password (optional)")
    args = parser.parse_args()

    if args.spec:
        payload = json.loads(args.spec)
    elif args.spec_file:
        with open(args.spec_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    else:
        parser.error("provide --spec or --spec-file")
    quota = json.loads(args.quota) if args.quota else None

    # Accept either a bare spec or a full request envelope (agent-request.json)
    if isinstance(payload, dict) and "spec" in payload:
        action = payload.get("action", args.action)
        agent_uri = payload.get("agent_uri", args.agent)
        capability = payload.get("capability", args.capability)
        environment = payload.get("environment")
        nonce = payload.get("nonce") or uuid.uuid4().hex
        spec = payload["spec"]
    else:
        action, agent_uri, capability = args.action, args.agent, args.capability
        environment, nonce = payload.get("environment"), None
        spec = payload
        if nonce is None:
            nonce = uuid.uuid4().hex

    agent_priv, agent_pub = demo_agent()
    identity = IdentityMapper()
    identity.register(agent_uri, agent_pub)
    if args.username:
        identity.bind(args.username, agent_uri)

    capabilities = CapabilityMapper()
    capabilities.grant_role(agent_uri, "ml-engineer")

    import os

    policy_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "policies")
    policies = PolicyEvaluator(policy_dir)

    node_priv, node_pub = demo_agent()
    chain = ProvenanceChain(target=f"chain://morpheus/{agent_uri.split('://')[1]}")
    client = GovernedClient(
        args.endpoint, identity, capabilities, policies, chain, node_priv, node_pub
    )

    if args.username:
        client.authenticate(args.username, args.password or "")
        resolved = identity.resolve_agent(args.username)
        if resolved is None:
            print(f"no agent:// bound to Morpheus user {args.username}")
            raise SystemExit(2)
        agent_uri = resolved

    request = GovernedRequest(
        action=action,
        agent_uri=agent_uri,
        capability=capability,
        spec=spec,
        nonce=nonce,
        environment=environment,
    )
    request.signature = sign(canonical_json(request.message()), agent_priv)

    result = client.govern(request, quota=quota)
    print(json.dumps(result, indent=2, default=vars))
    if result.decision != "ALLOW":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
