#!/usr/bin/env python3
"""Test cognitive lease lifecycle for ephemeral agents."""

import json
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class LeaseContract:
    lease_id: str
    agent_id: str
    resource_uri: str
    ttl_seconds: int
    created_at: float = field(default_factory=time.time)
    renewed_at: float = field(default_factory=time.time)
    revoked: bool = False

    def is_expired(self) -> bool:
        return time.time() > self.renewed_at + self.ttl_seconds

    def renew(self, extra_ttl: int = 0) -> None:
        self.renewed_at = time.time()
        if extra_ttl:
            self.ttl_seconds = extra_ttl

    def revoke(self) -> None:
        self.revoked = True


class LeaseManager:
    def __init__(self, default_ttl: int = 300):
        self.leases: dict[str, LeaseContract] = {}
        self.default_ttl = default_ttl
        self._history: list[dict] = []

    def create(self, agent_id: str, resource_uri: str, ttl: Optional[int] = None) -> LeaseContract:
        lease_id = f"lease-{random.randint(10000,99999)}"
        contract = LeaseContract(
            lease_id=lease_id,
            agent_id=agent_id,
            resource_uri=resource_uri,
            ttl_seconds=ttl or self.default_ttl,
        )
        self.leases[lease_id] = contract
        self._history.append({"action": "create", "lease_id": lease_id, "agent_id": agent_id,
                              "resource_uri": resource_uri, "ttl": contract.ttl_seconds,
                              "timestamp": contract.created_at})
        return contract

    def renew(self, lease_id: str, extra_ttl: int = 0) -> Optional[LeaseContract]:
        contract = self.leases.get(lease_id)
        if contract and not contract.revoked and not contract.is_expired():
            contract.renew(extra_ttl)
            self._history.append({"action": "renew", "lease_id": lease_id, "ttl": contract.ttl_seconds,
                                  "timestamp": contract.renewed_at})
            return contract
        return None

    def revoke(self, lease_id: str) -> bool:
        contract = self.leases.get(lease_id)
        if contract:
            contract.revoke()
            self._history.append({"action": "revoke", "lease_id": lease_id, "timestamp": time.time()})
            return True
        return False

    def collect_expired(self) -> list[str]:
        expired = [lid for lid, c in self.leases.items() if c.is_expired() and not c.revoked]
        for lid in expired:
            self._history.append({"action": "expire", "lease_id": lid, "timestamp": time.time()})
        return expired

    def report(self) -> dict:
        now = time.time()
        active = [c for c in self.leases.values() if not c.is_expired() and not c.revoked]
        expired = [c for c in self.leases.values() if c.is_expired() and not c.revoked]
        revoked = [c for c in self.leases.values() if c.revoked]
        return {
            "total_leases": len(self.leases),
            "active": len(active),
            "expired": len(expired),
            "revoked": len(revoked),
            "history_count": len(self._history),
        }

    def to_json(self) -> str:
        return json.dumps({
            "leases": {lid: {"agent_id": c.agent_id, "resource_uri": c.resource_uri,
                             "ttl": c.ttl_seconds, "revoked": c.revoked,
                             "expired": c.is_expired()}
                       for lid, c in self.leases.items()},
            "history": self._history[-50:],
        }, indent=2)


def test_basic_lifecycle():
    mgr = LeaseManager(default_ttl=1)
    c = mgr.create("agent-finance", "lease://agent/finance")
    assert not c.is_expired()
    assert c.lease_id in mgr.leases
    mgr.revoke(c.lease_id)
    assert mgr.leases[c.lease_id].revoked
    print("[PASS] basic_lifecycle")


def test_expiry():
    mgr = LeaseManager(default_ttl=0)
    c = mgr.create("agent-expire", "lease://agent/expire")
    assert c.is_expired()
    expired = mgr.collect_expired()
    assert c.lease_id in expired
    print("[PASS] expiry")


def test_renew():
    mgr = LeaseManager(default_ttl=10)
    c = mgr.create("agent-renew", "lease://agent/renew")
    mgr.renew(c.lease_id, extra_ttl=20)
    assert mgr.leases[c.lease_id].ttl_seconds == 20
    print("[PASS] renew")


def test_stress():
    mgr = LeaseManager(default_ttl=300)
    n = 1000
    for i in range(n):
        mgr.create(f"agent-{i}", f"lease://agent/resource-{i}")
    assert len(mgr.leases) == n
    report = mgr.report()
    assert report["active"] == n
    mgr.collect_expired()
    print(f"[PASS] stress ({n} leases)")


def test_uri_scheme_compliance():
    mgr = LeaseManager()
    c = mgr.create("agent-kyc", "lease://kyc/verification-42")
    assert c.resource_uri.startswith("lease://")
    assert "kyc" in c.resource_uri
    print("[PASS] uri_scheme_compliance")


if __name__ == "__main__":
    test_basic_lifecycle()
    test_expiry()
    test_renew()
    test_stress()
    test_uri_scheme_compliance()
    print("\nAll cognitive lease tests passed.")
