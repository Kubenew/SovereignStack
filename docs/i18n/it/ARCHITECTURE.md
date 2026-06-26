# Architettura di SovereignStack

**Revisione:** 1.0 — Maggio 2026  
**Stato:** Documento vivo

---

## 1. Panoramica del sistema

SovereignStack è una piattaforma infrastrutturale di IA sovrana a strati. Ogni strato ha confini, API e contratti di sicurezza ben definiti. I dati fluiscono rigorosamente verso l'alto attraverso gateway autenticati e regolati da policy.

## 2. Sottosistemi principali

### 2.1 Runtime Sovrano
Strato di esecuzione dell'IA. Responsabile del caricamento dei modelli, inferenza, pianificazione e isolamento delle risorse.

### 2.2 Strato di Memoria e Coordinazione
Archiviazione persistente, crittografata e distribuita per vettori, cache KV e sincronizzazione dello stato.

### 2.3 Strato di Identità e Sicurezza
Identità Zero Trust per nodi, carichi di lavoro e utenti.

### 2.4 Strato di Federazione e Mesh
Comunicazione inter-nodo, scoperta e sincronizzazione per distribuzioni multi-nodo.

## 3. Profili di distribuzione

| Profilo | Target | Particolarità |
|---------|--------|--------------|
| Edge | Dispositivi ARM, IoT | Inferenza CPU, locale, disconnesso |
| Air-Gapped | Reti isolate | GPU + CPU, AES-256 + TPM, senza WAN |
| Datacenter | Cluster GPU | Multi-GPU vLLM, DB distribuita |
| Personale | Laptop, homelab | CPU/GPU, FS locale, VPN opzionale |

---

*Vedere la [versione inglese canonica](/ARCHITECTURE.md) per riferimento.*
