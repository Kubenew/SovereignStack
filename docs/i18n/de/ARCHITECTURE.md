# SovereignStack-Architektur

**Revision:** 1.0 — Mai 2026  
**Status:** Lebendes Dokument

---

## 1. Systemüberblick

SovereignStack ist eine geschichtete, souveräne KI-Infrastrukturplattform. Jede Schicht hat klar definierte Grenzen, APIs und Sicherheitsverträge. Daten fließen strikt aufwärts durch authentifizierte, richtliniengeschützte Gateways.

```
                     ┌──────────────────────────────────────┐
                     │           ANWENDUNGEN                 │
                     │  OpenAI SDK / LangChain / Benutzerdef.│
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │         AUTONOME AGENTEN              │
                     │  Lebenszyklus · Planung · Speicher    │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │         KI-LAUFZEITSCHICHT            │
                     │  vLLM · llama.cpp · Modell-Router     │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │     SPEICHER & KOORDINATION           │
                     │  Vektordatenbank · KV-Cache · Sync    │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │      IDENTITÄT & SICHERHEIT          │
                     │  Keycloak OIDC · OPA · RBAC · mTLS   │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │    FÖDERATION & MESH-NETZWERK        │
                     │  Knoten-Sync · Discovery · Routing    │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │      CONTAINER / VM-LAUFZEIT         │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │       HOST-BETRIEBSSYSTEM            │
                     └──────────────┬───────────────────────┘
                     ┌──────────────▼───────────────────────┐
                     │            HARDWARE                  │
                     │  NVIDIA CUDA · Apple Metal · CPU     │
                     │  TPM 2.0 · SGX · SEV-SNP             │
                     └──────────────────────────────────────┘
```

## 2. Kernsubsysteme

### 2.1 Sovereign Runtime
Die KI-Ausführungsschicht. Verantwortlich für Modellladung, Inferenz, Planung und Ressourcenisolierung.

### 2.2 Speicher- & Koordinationsschicht
Beständiger, verschlüsselter, verteilter Speicher für Vektoren, KV-Caches und Zustandssynchronisation.

### 2.3 Identitäts- & Sicherheitsschicht
Null-Vertrauen-Identität für Knoten, Arbeitslasten und Benutzer.

### 2.4 Föderations- & Mesh-Schicht
Kommunikation zwischen Knoten, Erkennung und Synchronisation für Multi-Node-Bereitstellungen.

## 3. Vertrauensgrenzen

Das System definiert zwei Vertrauensgrenzen: Gateway (validiert JWT, wertet OPA-Richtlinien aus) und Hardware (TPM-gebundene Verschlüsselungsschlüssel, unveränderliche Audit-Zone).

## 4. Bereitstellungsprofile

| Profil | Ziel | Besonderheit |
|--------|------|-------------|
| Edge | ARM-Geräte, IoT | CPU-Inferenz, lokal, offline |
| Air-Gapped | Isolierte Netzwerke | GPU + CPU, AES-256 + TPM, kein WAN |
| Rechenzentrum | GPU-Cluster | Multi-GPU vLLM, verteilte DB |
| Persönlich | Laptop, Homelab | CPU/GPU, lokales FS, optionales VPN |

---

*Siehe [English (canonical)](/ARCHITECTURE.md) für die Referenzversion.*
