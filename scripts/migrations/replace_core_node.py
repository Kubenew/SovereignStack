import os

files = [
    "README.md",
    "v0.5-Verification-Gate.md",
    "conformance/README.md",
    "conformance/profiles/README.md",
    "conformance/profiles/example-profile.yaml",
    "conformance/profiles/agent-node.yaml",
    "conformance/profiles/federation-node.yaml",
    "conformance/profiles/knowledge-node.yaml",
    "conformance/tests/rfc/0010-conformance-framework/test_conformance_framework.py",
    "rfcs/RFC-0010-conformance-framework.md",
    "RELEASE-v0.3.0.md",
    "reference-node/src/main.rs",
    "verify.sh",
    "tools/ss-conformance.py"
]

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if "core-node" in content:
            new_content = content.replace("core-node", "core-0.1")
            # The user specifically mentioned: "The canonical profile will be profiles/core/0.1.yaml".
            # If the text has "conformance/profiles/core-0.1.yaml", it should become "profiles/core/0.1.yaml"
            new_content = new_content.replace("conformance/profiles/core-0.1.yaml", "profiles/core/0.1.yaml")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    else:
        print(f"File not found: {filepath}")
