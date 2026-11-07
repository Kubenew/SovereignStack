"""
Hardware telemetry and detection probe for AWS Neuron devices.
Supports discovery via neuron-ls, device nodes, and AWS EC2 instance metadata.
"""

import json
import os
import platform
import re
import subprocess
from typing import Dict, Any, List, Optional, Callable


class NeuronHardwareDetector:
    """
    Scans host environment for AWS Neuron devices and topology.
    """

    INSTANCE_PROFILES = {
        # Trainium 1
        "trn1.2xlarge": {"cores": 2, "devices": 1, "generation": "NeuronCore-v2", "mem_gb": 32},
        "trn1.32xlarge": {"cores": 32, "devices": 16, "generation": "NeuronCore-v2", "mem_gb": 512},
        "trn1n.32xlarge": {"cores": 32, "devices": 16, "generation": "NeuronCore-v2", "mem_gb": 512},
        # Inferentia 2
        "inf2.xlarge": {"cores": 2, "devices": 1, "generation": "NeuronCore-v2", "mem_gb": 32},
        "inf2.8xlarge": {"cores": 2, "devices": 1, "generation": "NeuronCore-v2", "mem_gb": 32},
        "inf2.24xlarge": {"cores": 12, "devices": 6, "generation": "NeuronCore-v2", "mem_gb": 192},
        "inf2.48xlarge": {"cores": 24, "devices": 12, "generation": "NeuronCore-v2", "mem_gb": 384},
        # Trainium 2
        "trn2.48xlarge": {"cores": 64, "devices": 16, "generation": "NeuronCore-v3", "mem_gb": 1024},
        # Inferentia 1 (Legacy)
        "inf1.xlarge": {"cores": 4, "devices": 1, "generation": "NeuronCore-v1", "mem_gb": 8},
        "inf1.2xlarge": {"cores": 4, "devices": 1, "generation": "NeuronCore-v1", "mem_gb": 8},
        "inf1.6xlarge": {"cores": 16, "devices": 4, "generation": "NeuronCore-v1", "mem_gb": 32},
        "inf1.24xlarge": {"cores": 64, "devices": 16, "generation": "NeuronCore-v1", "mem_gb": 128},
    }

    def __init__(self, command_runner: Optional[Callable[[List[str]], subprocess.CompletedProcess]] = None):
        self._runner = command_runner or subprocess.run

    def detect(self) -> Dict[str, Any]:
        """
        Perform complete hardware topology scan.
        """
        # 1. Try neuron-ls JSON
        devices = self._probe_neuron_ls()
        if devices:
            total_cores = sum(d.get("cores", 0) for d in devices)
            total_mem = sum(d.get("memory_gb", 0.0) for d in devices)
            sku = self._detect_instance_sku()
            gen = devices[0].get("generation", "NeuronCore-v2")
            return {
                "available": True,
                "device_count": len(devices),
                "total_cores": total_cores,
                "total_memory_gb": round(total_mem, 1),
                "generation": gen,
                "instance_sku": sku,
                "devices": devices,
                "discovery_method": "neuron-ls",
            }

        # 2. Try sysfs device inspection
        sysfs_devs = self._probe_sysfs()
        if sysfs_devs:
            sku = self._detect_instance_sku()
            prof = self.INSTANCE_PROFILES.get(sku, {})
            return {
                "available": True,
                "device_count": len(sysfs_devs),
                "total_cores": prof.get("cores", len(sysfs_devs) * 2),
                "total_memory_gb": prof.get("mem_gb", len(sysfs_devs) * 32),
                "generation": prof.get("generation", "NeuronCore-v2"),
                "instance_sku": sku,
                "devices": sysfs_devs,
                "discovery_method": "sysfs",
            }

        # 3. Check instance SKU heuristic
        sku = self._detect_instance_sku()
        if sku in self.INSTANCE_PROFILES:
            prof = self.INSTANCE_PROFILES[sku]
            return {
                "available": True,
                "device_count": prof["devices"],
                "total_cores": prof["cores"],
                "total_memory_gb": prof["mem_gb"],
                "generation": prof["generation"],
                "instance_sku": sku,
                "devices": [{"id": i, "cores": prof["cores"] // prof["devices"]} for i in range(prof["devices"])],
                "discovery_method": "sku_heuristic",
            }

        return {
            "available": False,
            "device_count": 0,
            "total_cores": 0,
            "total_memory_gb": 0.0,
            "generation": "unknown",
            "instance_sku": "unknown",
            "devices": [],
            "discovery_method": "none",
        }

    def _probe_neuron_ls(self) -> List[Dict[str, Any]]:
        try:
            res = self._runner(["neuron-ls", "-j"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout)
                devices = []
                for entry in raw:
                    dev_id = entry.get("neuron_device_id", 0)
                    cores = entry.get("neuron_core_count", 2)
                    mem_bytes = entry.get("memory_size", 0)
                    gen = "NeuronCore-v1" if "inferentia" in str(entry).lower() else "NeuronCore-v2"
                    devices.append({
                        "device_id": dev_id,
                        "cores": cores,
                        "memory_gb": round(mem_bytes / (1024 ** 3), 1),
                        "pci_bdf": entry.get("pci_bdf", "unknown"),
                        "generation": gen,
                    })
                return devices
        except Exception:
            pass
        return []

    def _probe_sysfs(self) -> List[Dict[str, Any]]:
        devices = []
        if platform.system() == "Linux":
            dev_dir = "/dev"
            if os.path.isdir(dev_dir):
                for name in os.listdir(dev_dir):
                    if name.startswith("neuron"):
                        devices.append({"name": name, "path": os.path.join(dev_dir, name)})
        return devices

    def _detect_instance_sku(self) -> str:
        # Check environment variable override
        if "AWS_INSTANCE_TYPE" in os.environ:
            return os.environ["AWS_INSTANCE_TYPE"].strip()
        # Read DMI product name on Linux
        dmi_path = "/sys/devices/virtual/dmi/id/product_name"
        if os.path.exists(dmi_path):
            try:
                with open(dmi_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    for sku in self.INSTANCE_PROFILES:
                        if sku in content.lower():
                            return sku
            except Exception:
                pass
        return "unknown"

