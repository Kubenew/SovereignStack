# Architektura SovereignStacku

**Revize:** 1.0 — Květen 2026  
**Stav:** Živý dokument

---

## 1. Přehled systému

SovereignStack je vrstvená suverénní AI infrastrukturní platforma. Každá vrstva má dobře definované hranice, API a bezpečnostní kontrakty. Data proudí striktně vzhůru přes autentizované brány řízené politikami.

## 2. Hlavní subsystémy

### 2.1 Suverénní runtime
Vrstva pro provádění AI. Zodpovídá za načítání modelů, inferenci, plánování a izolaci zdrojů.

### 2.2 Vrstva paměti a koordinace
Perzistentní, šifrované, distribuované úložiště pro vektory, KV cache a synchronizaci stavu.

### 2.3 Vrstva identity a zabezpečení
Zero-trust identita pro uzly, úlohy a uživatele.

### 2.4 Vrstva federace a mesh sítě
Meziuzlová komunikace, objevování a synchronizace pro multi-uzlová nasazení.

## 3. Profily nasazení

| Profil | Cíl | Specifikum |
|--------|-----|------------|
| Edge | ARM zařízení, IoT | CPU inference, lokální, offline |
| Air-Gapped | Izolované sítě | GPU + CPU, AES-256 + TPM, bez WAN |
| Datové centrum | GPU clustery | Multi-GPU vLLM, distribuovaná DB |
| Osobní | Notebook, homelab | CPU/GPU, lokální FS, volitelné VPN |

---

*Viz [anglická kanonická verze](/ARCHITECTURE.md) pro referenci.*
