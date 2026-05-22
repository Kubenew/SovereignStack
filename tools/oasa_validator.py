import sys, yaml

STRICT_REQUIRED = {
    ("node","air_gapped"): True,
    ("node","tpm_required"): True,
    ("node","encryption"): "AES-256-GCM"
}

def get_path(obj, path):
    cur = obj
    for p in path:
        if p not in cur:
            return None
        cur = cur[p]
    return cur

def validate_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    errors = []
    for p, expected in STRICT_REQUIRED.items():
        actual = get_path(data, list(p))
        if actual != expected:
            errors.append(f"{'.'.join(p)} must be {expected}, got {actual}")

    if errors:
        print("OASA VALIDATION FAILED")
        for e in errors:
            print(" -", e)
        return 2

    print("OASA VALIDATION PASSED")
    return 0

def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/oasa_validator.py validate sovereign-stack.yaml")
        sys.exit(1)

    if sys.argv[1] != "validate":
        print("Unknown command")
        sys.exit(1)

    sys.exit(validate_manifest(sys.argv[2]))

if __name__ == "__main__":
    main()
