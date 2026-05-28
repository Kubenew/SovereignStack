import sys

def main():
    print("WARNING: oasa_validator.py is DEPRECATED and has been removed.", file=sys.stderr)
    print("Please use the modern compliance validation tool instead:", file=sys.stderr)
    print("  python tools/validate_compliance.py <manifest.yaml>", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
