# Reference Architectures

This directory contains deployment-ready reference architectures showing how SovereignStack maps to real-world industry deployments.

Each document includes:
- **Architecture diagram** (Mermaid) showing component topology
- **Component mapping** from SovereignStack crates to domain roles
- **Digital twin model** showing which `://` schemes are primary
- **Compliance requirements** and how SovereignStack satisfies them
- **Deployment considerations** for production environments

## Available Architectures

| Industry | Document | Primary Twins | Key Modules |
|----------|----------|---------------|-------------|
| [Banking](banking.md) | Core banking, payments, regulatory reporting | `bank://`, `person://`, `portfolio://` | payments, settlement, treasury, accounting |
| [Insurance](insurance.md) | Underwriting, claims, risk modeling | `company://`, `person://` | insurance, risk, fin_compliance |
| [Government](government.md) | Citizen services, inter-agency federation | `person://`, `company://` | fin_identity, fin_compliance |
| [Healthcare](healthcare.md) | Patient sovereignty, clinical decision support | `person://`, `hospital://` | fin_identity, fin_compliance |
| [Manufacturing](manufacturing.md) | Digital twin factories, supply chain | `factory://`, `vehicle://`, `company://` | assets, accounting |
