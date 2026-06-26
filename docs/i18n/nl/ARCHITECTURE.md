# SovereignStack-architectuur

**Revisie:** 1.0 — Mei 2026  
**Status:** Levend document

---

## 1. Systeemoverzicht

SovereignStack is een gelaagd soeverein AI-infrastructuurplatform. Elke laag heeft goed gedefinieerde grenzen, API's en beveiligingscontracten. Gegevens stromen strikt omhoog via geverifieerde en door beleid geregelde gateways.

## 2. Kerndomeinen

### 2.1 Soevereine Runtime
AI-uitvoeringslaag. Verantwoordelijk voor modelladen, inferentie, planning en resource-isolatie.

### 2.2 Geheugen- en Coördinatielaag
Persistente, versleutelde, gedistribueerde opslag voor vectoren, KV-caches en statussynchronisatie.

### 2.3 Identiteits- en Beveiligingslaag
Zero-trust identiteit voor nodes, workloads en gebruikers.

### 2.4 Federatie- en Mesh-laag
Inter-node communicatie, ontdekking en synchronisatie voor multi-node implementaties.

## 3. Implementatieprofielen

| Profiel | Doel | Kenmerk |
|---------|------|---------|
| Edge | ARM-apparaten, IoT | CPU-inferentie, lokaal, offline |
| Air-Gapped | Geïsoleerde netwerken | GPU + CPU, AES-256 + TPM, geen WAN |
| Datacenter | GPU-clusters | Multi-GPU vLLM, gedistribueerde DB |
| Persoonlijk | Laptop, homelab | CPU/GPU, lokaal FS, optionele VPN |

---

*Zie de [Engelse canonieke versie](/ARCHITECTURE.md) voor referentie.*
