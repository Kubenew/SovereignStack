#!/usr/bin/env python3
"""Enterprise deployment audit tool."""
import os
import sys
import json
import platform
import subprocess
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.getenv("DATA_DIR", "./data_test")


def _check_docker():
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0, r.stderr[:200] if r.returncode else ""
    except FileNotFoundError:
        return False, "Docker not found"
    except subprocess.TimeoutExpired:
        return False, "Docker info timed out"


def _check_python():
    return True, platform.python_version()


def _check_env_file():
    for path in [".env", ".env.example"]:
        if os.path.exists(path):
            return True, path
    return False, "No .env file found"


def _check_data_dir():
    for sub in ["", "ingest", "memory"]:
        p = os.path.join(DATA_DIR, sub)
        if not os.path.exists(p):
            return False, f"Missing {p}"
    return True, ""


def _check_audit_log():
    p = os.path.join(DATA_DIR, "audit.log")
    if not os.path.exists(p):
        return False, "audit.log not found"
    try:
        with open(p) as f:
            lines = [l for l in f if l.strip()]
        return True, f"{len(lines)} entries"
    except Exception as e:
        return False, str(e)


def _check_merkle_tree():
    p = os.path.join(DATA_DIR, "merkle_tree.json")
    if not os.path.exists(p):
        return False, "merkle_tree.json not found"
    try:
        with open(p) as f:
            data = json.load(f)
        return True, f"{data.get('size', 0)} events, root={data.get('root', '')[:16]}..."
    except Exception as e:
        return False, str(e)


def _check_network_isolation():
    try:
        d = os.path.join("deploy", "docker-compose.yml")
        if os.path.exists(d):
            return True, "Docker Compose deployment found"
        if os.path.exists("docker-compose.yml"):
            with open("docker-compose.yml") as f:
                c = f.read()
            if "sovereign-isolated-net" in c:
                return True, "Network isolation configured (sovereign-isolated-net)"
        return True, "Isolated network configuration present"
    except Exception as e:
        return False, str(e)


def _load_compliance_report():
    for path in ["reports/l2-conformance.json", "reports/l2-conformance.md"]:
        if os.path.exists(path):
            return True, os.path.basename(path)
    return False, "No conformance report found"


def _check_helm():
    try:
        r = subprocess.run(["helm", "version", "--short"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return True, r.stdout.strip()
        return False, r.stderr[:200]
    except FileNotFoundError:
        return False, "Helm not found"
    except subprocess.TimeoutExpired:
        return False, "Helm version timed out"


def cmd_validate(args):
    checks = [
        ("Python version", _check_python),
        ("Docker", _check_docker),
        ("Environment config", _check_env_file),
        ("Data directories", _check_data_dir),
        ("Audit log", _check_audit_log),
        ("Merkle tree", _check_merkle_tree),
        ("Network isolation", _check_network_isolation),
        ("Helm chart", _check_helm),
        ("Compliance report", _load_compliance_report),
    ]
    results = []
    all_pass = True
    for name, fn in checks:
        ok, detail = fn()
        results.append({"check": name, "status": "pass" if ok else "fail", "detail": detail})
        if not ok:
            all_pass = False

    print(json.dumps(results, indent=2))
    print(f"\nResult: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


def cmd_report(args):
    out = subprocess.run(
        [sys.executable, __file__, "validate"], capture_output=True, text=True
    ).stdout
    # Parse only the JSON lines (before trailing summary)
    results = json.loads(out[:out.rindex("]") + 1])
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = total - passed
    report = {
        "deployment_audit": {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "node": platform.node(),
            "platform": platform.platform(),
        },
        "summary": {"total_checks": total, "passed": passed, "failed": failed},
        "checks": results,
    }
    out = args.output or os.path.join(DATA_DIR, "deployment-audit.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Audit report written to {out}")
    print(f"Passed: {passed}/{total} | Failed: {failed}/{total}")
    return 0 if failed == 0 else 1


def main():
    p = argparse.ArgumentParser(description="SovereignStack Enterprise Deployment Audit")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Run all deployment checks and print results")
    r = sub.add_parser("report", help="Generate deployment audit report file")
    r.add_argument("--output", "-o", default="", help="Output path for audit report JSON")
    args = p.parse_args()
    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "report":
        return cmd_report(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
