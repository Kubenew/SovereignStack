#!/usr/bin/env python3
"""Live Merkle audit log tailer for the SovereignStack compliance fabric."""

import os
import json
import time
from typing import Generator


class AuditLogFollower:
    def __init__(self, log_path: str = "/var/log/sovereignstack/audit.log"):
        self.log_path = log_path

    def follow(self) -> Generator[dict, None, None]:
        if not os.path.exists(self.log_path):
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "w") as f:
                f.write("")

        with open(self.log_path, "r") as file:
            file.seek(0, os.SEEK_END)
            while True:
                line = file.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                try:
                    yield json.loads(line.strip())
                except json.JSONDecodeError:
                    continue


if __name__ == "__main__":
    print("Subscribing to live Merkle audit event stream...")
    follower = AuditLogFollower()
    with open(follower.log_path, "a") as f:
        f.write(json.dumps({"event_id": "0x1a2b", "type": "POLICY_VERIFICATION", "status": "ALLOWED"}) + "\n")

    for entry in follower.follow():
        print(f"Audit Event | Type: {entry.get('type')} | Status: {entry.get('status')}")
        break
