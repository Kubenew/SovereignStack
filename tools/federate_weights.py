#!/usr/bin/env python3
"""
Secure Weight Federation CLI — shard, distribute, and test federated models.

Usage:
  python tools/federate_weights.py shard --model weights.npy --output-dir ./shards --num-shards 4
  python tools/federate_weights.py distribute --shard-dir ./shards --nodes http://node1:8087,http://node2:8087
  python tools/federate_weights.py test --model-name my-model --nodes http://node1:8087
"""
import os
import sys
import json
import uuid
import base64
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _load_weights(path):
    import numpy as np
    data = np.load(path)
    if isinstance(data, np.ndarray):
        return data
    return data[list(data.keys())[0]]


def cmd_shard(args):
    import numpy as np
    weights = _load_weights(args.model)
    total_rows = weights.shape[0]
    shard_size = total_rows // args.num_shards
    shards = []
    os.makedirs(args.output_dir, exist_ok=True)
    for i in range(args.num_shards):
        start = i * shard_size
        end = start + shard_size if i < args.num_shards - 1 else total_rows
        shard = weights[start:end]
        shard_path = os.path.join(args.output_dir, f"shard-{i}.npy")
        np.save(shard_path, shard)
        shard_b64 = base64.b64encode(shard.tobytes()).decode()
        shard_payload = json.dumps(shard.tolist())
        shard_json_path = os.path.join(args.output_dir, f"shard-{i}.json")
        with open(shard_json_path, "w") as f:
            json.dump(json.loads(shard_payload), f)
        shards.append({
            "index": i,
            "rows": shard.shape[0],
            "cols": shard.shape[1],
            "npy_path": shard_path,
            "json_path": shard_json_path,
        })
        print(f"  Shard {i}: {shard.shape[0]}x{shard.shape[1]} -> {shard_path}")
    manifest = {
        "model_name": args.name or os.path.splitext(os.path.basename(args.model))[0],
        "model_version": args.version or "1.0.0",
        "num_shards": args.num_shards,
        "total_rows": total_rows,
        "cols": weights.shape[1],
        "shards": shards,
    }
    manifest_path = os.path.join(args.output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote manifest to {manifest_path}")
    print(f"Total weights: {total_rows}x{weights.shape[1]} = {weights.size} parameters")
    return 0


def cmd_distribute(args):
    manifest_path = os.path.join(args.shard_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: manifest.json not found in {args.shard_dir}")
        return 1
    with open(manifest_path) as f:
        manifest = json.load(f)
    nodes = args.nodes.split(",")
    if len(nodes) < manifest["num_shards"]:
        print(f"Error: Need {manifest['num_shards']} nodes, got {len(nodes)}")
        return 1
    import requests
    model_name = manifest["model_name"]
    model_version = manifest["model_version"]
    for i, node in enumerate(nodes):
        node = node.strip()
        shard_info = manifest["shards"][i]
        shard_json_path = os.path.join(args.shard_dir, f"shard-{i}.json")
        if not os.path.exists(shard_json_path):
            print(f"Error: {shard_json_path} not found")
            continue
        with open(shard_json_path) as f:
            shard_weights = json.load(f)
        shard_id = f"{model_name}-v{model_version}-shard-{i}"
        with open(os.path.join(args.shard_dir, f"shard-{i}.npy"), "rb") as npy_file:
            import numpy as np
            shard_np = np.load(npy_file)
        input_dim = shard_np.shape[1]
        reg_resp = requests.post(
            f"{node}/federation/weights/register",
            json={
                "model_name": model_name,
                "model_version": model_version,
                "shard_index": i,
                "total_shards": manifest["num_shards"],
                "layers": [f"layer_{i}"],
                "node_endpoint": node,
                "input_shape": [input_dim],
                "output_shape": [shard_np.shape[0]],
            },
            timeout=10,
        )
        if reg_resp.status_code != 200:
            print(f"  Node {node}: registration failed: {reg_resp.text}")
            continue
        weights_b64 = base64.b64encode(json.dumps(shard_weights).encode()).decode()
        store_resp = requests.post(
            f"{node}/federation/weights/store",
            json={
                "shard_id": shard_id,
                "weights_b64": weights_b64,
                "metadata": {"source": args.shard_dir, "shard_index": i},
            },
            timeout=30,
        )
        if store_resp.status_code == 200:
            print(f"  Shard {i} -> {node}: stored (checksum: {store_resp.json()['checksum'][:16]}...)")
        else:
            print(f"  Shard {i} -> {node}: failed: {store_resp.text}")
    return 0


def cmd_test(args):
    import requests
    manifest_path = os.path.join(os.path.dirname(args.nodes.split(",")[0].strip()),
                                  "..", "data_test", "shards", "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        cols = manifest.get("cols", 64)
    else:
        cols = 64
    import numpy as np
    dummy_input = np.random.randn(1, cols).tolist()
    node = args.nodes.split(",")[0].strip()
    if not node.startswith("http"):
        node = f"http://{node}"
    resp = requests.post(
        f"{node}/federation/weights/inference",
        json={
            "model_name": args.model_name,
            "model_version": args.model_version or "1.0.0",
            "input_data": dummy_input,
        },
        timeout=60,
    )
    if resp.status_code == 200:
        result = resp.json()
        output = result["output"]
        print(f"Inference result: {len(output)}x{len(output[0]) if output else 0}")
        print(f"Shards used: {result['shards_used']}")
        print(f"Request ID: {result['request_id']}")
        return 0
    else:
        print(f"Inference failed: {resp.status_code} {resp.text}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Secure Weight Federation CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("shard", help="Split model weights into shards")
    s.add_argument("--model", required=True, help="Path to .npy weights file")
    s.add_argument("--output-dir", default="./shards", help="Output directory for shards")
    s.add_argument("--num-shards", type=int, default=2, help="Number of shards")
    s.add_argument("--name", help="Model name (default: filename)")
    s.add_argument("--version", default="1.0.0", help="Model version")
    d = sub.add_parser("distribute", help="Distribute shards to federation nodes")
    d.add_argument("--shard-dir", default="./shards", help="Directory with shard files")
    d.add_argument("--nodes", required=True, help="Comma-separated node URLs")
    t = sub.add_parser("test", help="Test sharded inference")
    t.add_argument("--model-name", required=True, help="Model name to test")
    t.add_argument("--model-version", default="1.0.0", help="Model version")
    t.add_argument("--nodes", default="http://localhost:8087", help="Node URL(s)")
    args = parser.parse_args()
    if args.command == "shard":
        return cmd_shard(args)
    elif args.command == "distribute":
        return cmd_distribute(args)
    elif args.command == "test":
        return cmd_test(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
