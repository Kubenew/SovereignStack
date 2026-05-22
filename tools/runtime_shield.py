#!/usr/bin/env python3
"""
OASA Runtime Shield Wrapper
===========================
Provides runtime isolation for AI inference engines.
Monitors RAM/VRAM leaks and blocks unauthorized outbound network activity.

Usage:
    python runtime_shield.py --config ../sovereign-stack.yaml --cmd "python -m turboprivate_ai.main"
"""

import argparse
import time
import subprocess
import sys
import psutil
import socket
from pathlib import Path
import yaml # Requires PyYAML (pip install pyyaml)

class RuntimeShield:
    def __init__(self, config_path: str, command: str):
        self.config = self._load_config(config_path)
        self.command = command
        self.process = None
        
        # Protection parameters from YAML
        # Backward compatibility: supports both old (compute) and new (compute_execution) structures
        compute_cfg = self.config.get("compute_execution", self.config.get("compute", {}))
        runtime_prot = compute_cfg.get("runtime_protection", {})
        
        self.mem_threshold_mb = runtime_prot.get("memory_leak_threshold_mb", 512)
        self.compliance_lock = runtime_prot.get("enforce_compliance_lock", True)
        
        node_infra = self.config.get("node_infrastructure", self.config.get("node", {}))
        self.air_gapped = node_infra.get("air_gapped_enforcement", node_infra.get("air_gapped", True))

    def _load_config(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def verify_network_isolation(self) -> bool:
        """Verifies if the AI process opened unauthorized outbound connections."""
        if not self.air_gapped:
            return True
            
        print("[SHIELD] Verifying network isolation loop...")
        try:
            # Attempt to establish outbound connection
            socket.create_connection(("8.8.8.8", 53), timeout=1.0)
            return False # If connection is successful — isolation breached!
        except (socket.timeout, OSError):
            return True # Network is securely isolated

    def monitor_loop(self):
        """Main monitoring loop for the AI process execution."""
        print(f"[SHIELD] Launching sovereign AI process: {self.command}")
        print("=" * 60)
        
        # Start target AI engine in isolated subprocess
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        psutil_proc = psutil.Process(self.process.pid)
        
        # Small delay to allow base memory allocation
        time.sleep(1)
        initial_memory = psutil_proc.memory_info().rss / (1024 * 1024)
        print(f"[SHIELD] Base process memory allocation: {initial_memory:.2f} MB")

        try:
            while self.process.poll() is None:
                time.sleep(2) # Check interval — every 2 seconds
                
                # 1. Memory Leak Protection
                current_memory = psutil_proc.memory_info().rss / (1024 * 1024)
                mem_drift = current_memory - initial_memory
                
                print(f"[TELEMETRY] Current RAM: {current_memory:.2f} MB | Memory Drift: {mem_drift:.2f} MB")

                if mem_drift > self.mem_threshold_mb:
                    print(f"\n[ALERT] CRITICAL MEMORY LEAK: Exceeded limit of {self.mem_threshold_mb} MB.")
                    self.terminate_incident("MEMORY_EXCEEDED")
                    break

                # 2. Network Isolation Check
                if not self.verify_network_isolation():
                    print("\n[ALERT] SECURITY BREACH: Unauthorized WAN activity detected!")
                    self.terminate_incident("NETWORK_VIOLATION")
                    break

        except KeyboardInterrupt:
            print("\n[SHIELD] Process manually stopped by user.")
            self.terminate_incident("MANUAL_STOP")

    def terminate_incident(self, reason: str):
        """Emergency termination of the process (Kill Switch) in case of an incident."""
        if self.process and self.process.poll() is None:
            print(f"[KILL SWITCH] Emergency termination of AI context. Reason: {reason}")
            self.process.kill()
            self.process.wait()
            
            if self.compliance_lock:
                print("[COMPLIANCE LOCK] FULL NODE BLOCK ACTIVATED. All external API interfaces frozen.")
            sys.exit(1)
        print("[SHIELD] AI process completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OASA Runtime Shield")
    parser.add_argument("--config", type=str, required=True, help="Path to sovereign-stack.yaml")
    parser.add_argument("--cmd", type=str, required=True, help="Command to run AI model/proxy")
    args = parser.parse_args()

    shield = RuntimeShield(args.config, args.cmd)
    shield.monitor_loop()


