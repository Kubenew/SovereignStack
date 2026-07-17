#!/usr/bin/env python3
"""Simulate cluster degradation and circuit breaker response."""

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MeshNode:
    node_id: str
    healthy: bool = True
    cpu_load: float = 0.0
    memory_used_mb: float = 0.0
    lease_count: int = 0


class DegradationSimulator:
    def __init__(self, node_count: int = 10):
        self.nodes = [MeshNode(node_id=f"node-{i}") for i in range(node_count)]
        self.history: list[dict] = []
        self.circuit_breaker_open = False

    def step(self) -> list[str]:
        events = []
        for node in self.nodes:
            if not node.healthy:
                continue
            # Random load fluctuation
            node.cpu_load = min(100, max(0, node.cpu_load + random.gauss(0, 5)))
            node.memory_used_mb = min(64000, max(0, node.memory_used_mb + random.gauss(0, 200)))

            # Random failures
            if node.cpu_load > 95 or node.memory_used_mb > 60000:
                node.healthy = False
                events.append(f"{node.node_id} FAILED (cpu={node.cpu_load:.1f}%, mem={node.memory_used_mb:.0f}MB)")
                if not self.circuit_breaker_open:
                    self.circuit_breaker_open = True
                    events.append("CIRCUIT BREAKER OPENED")

        self.history.append({
            "time": time.time(),
            "healthy_count": sum(1 for n in self.nodes if n.healthy),
            "nodes": [{"id": n.node_id, "healthy": n.healthy, "cpu": n.cpu_load, "mem": n.memory_used_mb}
                      for n in self.nodes],
            "circuit_breaker": self.circuit_breaker_open,
        })
        return events

    def repair(self, node_id: str) -> bool:
        for node in self.nodes:
            if node.node_id == node_id and not node.healthy:
                node.healthy = True
                node.cpu_load = random.uniform(10, 50)
                node.memory_used_mb = random.uniform(1000, 10000)
                return True
        return False

    def summary(self) -> dict:
        healthy = sum(1 for n in self.nodes if n.healthy)
        return {
            "total_nodes": len(self.nodes),
            "healthy": healthy,
            "failed": len(self.nodes) - healthy,
            "circuit_breaker_open": self.circuit_breaker_open,
            "steps_simulated": len(self.history),
            "avg_cpu": sum(n.cpu_load for n in self.nodes) / len(self.nodes),
            "avg_mem": sum(n.memory_used_mb for n in self.nodes) / len(self.nodes),
        }


def test_basic_degradation():
    sim = DegradationSimulator(node_count=5)
    for _ in range(10):
        events = sim.step()
        for e in events:
            print(f"  {e}")
    summary = sim.summary()
    print(f"  Summary: {summary['healthy']}/{summary['total_nodes']} healthy")
    print("[PASS] basic_degradation")


def test_repair():
    sim = DegradationSimulator(node_count=3)
    for _ in range(20):
        sim.step()
    for node in sim.nodes:
        if not node.healthy:
            assert sim.repair(node.node_id)
            assert node.healthy
            break
    print("[PASS] repair")


def test_circuit_breaker():
    sim = DegradationSimulator(node_count=1)
    for _ in range(100):
        events = sim.step()
        if any("CIRCUIT BREAKER" in e for e in events):
            break
    assert sim.circuit_breaker_open
    print("[PASS] circuit_breaker_triggers")


if __name__ == "__main__":
    test_basic_degradation()
    test_repair()
    test_circuit_breaker()
    print("\nAll mesh degradation tests passed.")
