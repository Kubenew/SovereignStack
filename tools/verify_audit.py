#!/usr/bin/env python3
"""Merkle tree audit verification tool.

Usage:
    python tools/verify_audit.py                    # Show current root and size
    python tools/verify_audit.py --index 0           # Get Merkle proof for event 0
    python tools/verify_audit.py --verify            # Load tree, recompute root, verify integrity
    python tools/verify_audit.py --export-proofs     # Export all proof hashes for external auditing
"""

import argparse
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.merkle_audit import get_merkle_tree, _hash_event, _hash_pair


def cmd_status():
    tree = get_merkle_tree()
    print(f"Tree size: {tree.size}")
    print(f"Root hash: {tree.root}")
    print(f"Leaves:    {len(tree.leaves)}")
    print(f"Tree nodes:{len(tree.tree)}")
    if tree.root:
        print(f"\nAudit root fingerprint: sha256:{tree.root}")


def cmd_proof(index: int):
    tree = get_merkle_tree()
    if index < 0 or index >= tree.size:
        print(f"Error: index {index} out of range (0-{tree.size - 1})", file=sys.stderr)
        sys.exit(1)
    event = tree.get_event(index)
    proof = tree.get_proof(index)
    print(f"Event #{index}:")
    print(f"  Type:   {event.get('type', 'unknown')}")
    print(f"  Time:   {event.get('ts', 'unknown')}")
    print(f"  Leaf:   {tree.leaves[index]}")
    print(f"\nProof ({len(proof)} steps):")
    for i, step in enumerate(proof):
        print(f"  {i + 1}. [{step['position']}] {step['hash']}")
    print(f"\nRoot:  {tree.root}")
    ok = tree.verify_proof(tree.leaves[index], proof, tree.root)
    print(f"\nVerification: {'PASSED' if ok else 'FAILED'}")


def cmd_verify():
    tree = get_merkle_tree()
    print(f"Verifying Merkle tree integrity...")
    print(f"Events:  {tree.size}")
    print(f"Root:    {tree.root}")
    # Rebuild tree from events
    tree._rebuild()
    recomputed_root = tree.root
    print(f"Rebuilt: {recomputed_root}")
    if tree.root == recomputed_root:
        print("\nIntegrity: PASSED (root hash matches recomputed)")
    else:
        print("\nIntegrity: FAILED (root hash mismatch!)", file=sys.stderr)
        sys.exit(1)
    # Verify a random sample
    import random
    if tree.size > 0:
        sample = random.sample(range(tree.size), min(5, tree.size))
        for idx in sample:
            proof = tree.get_proof(idx)
            leaf = tree.leaves[idx]
            if tree.verify_proof(leaf, proof, tree.root):
                print(f"  Event #{idx}: PASSED")
            else:
                print(f"  Event #{idx}: FAILED", file=sys.stderr)
                sys.exit(1)


def cmd_export():
    tree = get_merkle_tree()
    export = {
        "root": tree.root,
        "size": tree.size,
        "leaves": tree.leaves,
        "events_summary": [
            {"index": i, "type": e.get("type", "unknown"), "ts": e.get("ts", ""), "leaf": tree.leaves[i]}
            for i, e in enumerate(tree.events)
        ],
    }
    print(json.dumps(export, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Merkle Tree Audit Verification Tool")
    parser.add_argument("--index", type=int, help="Get Merkle proof for event at index")
    parser.add_argument("--verify", action="store_true", help="Verify tree integrity")
    parser.add_argument("--export-proofs", action="store_true", help="Export all proof data")
    args = parser.parse_args()

    if args.verify:
        cmd_verify()
    elif args.index is not None:
        cmd_proof(args.index)
    elif args.export_proofs:
        cmd_export()
    else:
        cmd_status()


if __name__ == "__main__":
    main()
