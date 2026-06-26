# Architektura SovereignStack

**Rewizja:** 1.0 — Maj 2026  
**Status:** Żywy dokument

---

## 1. Przegląd systemu

SovereignStack to warstwowa suwerenna platforma infrastruktury AI. Każda warstwa ma dobrze zdefiniowane granice, API i kontrakty bezpieczeństwa. Dane przepływają ściśle w górę przez uwierzytelnione bramy sterowane politykami.

## 2. Główne podsystemy

### 2.1 Suwerenne środowisko wykonawcze
Warstwa wykonawcza AI. Odpowiedzialna za ładowanie modeli, inferencję, planowanie i izolację zasobów.

### 2.2 Warstwa pamięci i koordynacji
Trwałe, szyfrowane, rozproszone przechowywanie dla wektorów, pamięci podręcznych KV i synchronizacji stanu.

### 2.3 Warstwa tożsamości i bezpieczeństwa
Tożsamość zero-trust dla węzłów, obciążeń i użytkowników.

### 2.4 Warstwa federacji i sieci mesh
Komunikacja międzywęzłowa, odkrywanie i synchronizacja dla wielowęzłowych wdrożeń.

## 3. Profile wdrożeniowe

| Profil | Cel | Cecha |
|--------|-----|-------|
| Edge | Urządzenia ARM, IoT | Inferencja CPU, lokalnie, offline |
| Air-Gapped | Sieci izolowane | GPU + CPU, AES-256 + TPM, brak WAN |
| Centrum danych | Klastry GPU | Multi-GPU vLLM, rozproszona baza |
| Osobisty | Laptop, homelab | CPU/GPU, lokalny FS, opcjonalne VPN |

---

*Patrz [kanoniczna wersja angielska](/ARCHITECTURE.md) jako referencja.*
