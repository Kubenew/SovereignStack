# OASA Certified Registry

This is the public registry of OASA-compatible, verified, and certified implementations.

## Certified (L3)

| Implementation | Type | Version | Certified Since | Badge |
|---------------|------|---------|----------------|-------|
| _None yet — be the first!_ | | | | |

## Verified (L2)

| Implementation | Type | Version | Verified Since | Badge |
|---------------|------|---------|----------------|-------|
| _None yet — be the first!_ | | | | |

## Compatible (L1)

| Implementation | Type | Version | Compatible Since | Badge |
|---------------|------|---------|-----------------|-------|
| _None yet — be the first!_ | | | | |

---

## How to Add Your Implementation

1. **Run the conformance test suite** at your target level:
   ```bash
   pip install -r requirements.txt
   python -m pytest tests/conformance/ -v --level L2
   ```

2. **Generate your compliance report**:
   ```bash
   python tools/generate_compliance_report.py --level L2 --output my-report.md
   ```

3. **Submit a PR** to this file adding your entry with:
   - Name and version of your implementation
   - Link to your conformance report
   - Contact email for verification
   - Badge level achieved

4. **Receive your badge** and be listed in the official OASA registry.

---

## License

Apache 2.0
