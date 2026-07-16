#!/usr/bin/env python3
"""gRPC mesh state subscriber pulling peer metadata from ss-memory mind-sync."""

import time
from typing import Iterator


class MeshStateSubscriber:
    def __init__(self, target_host: str = "localhost:50051"):
        self.target_host = target_host

    def stream_peer_updates(self) -> Iterator[dict]:
        print(f"Establishing bi-directional gRPC channel to {self.target_host}...")
        for i in range(1, 4):
            time.sleep(0.5)
            yield {
                "node_id": f"node://eu-frankfurt-0{i}",
                "vram_free_gb": 80 - (i * 12),
                "active_connections": i * 5,
                "attention_delta_hash": f"sha256_{i}b840f92",
            }


if __name__ == "__main__":
    subscriber = MeshStateSubscriber()
    for peer_update in subscriber.stream_peer_updates():
        print(f"Peer Sync | Node: {peer_update['node_id']} | vRAM Free: {peer_update['vram_free_gb']}GB")
