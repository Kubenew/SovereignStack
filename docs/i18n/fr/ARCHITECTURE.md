# Architecture SovereignStack

**Révision :** 1.0 — Mai 2026  
**Statut :** Document évolutif

---

## 1. Vue d'ensemble du système

SovereignStack est une plateforme d'infrastructure d'IA souveraine en couches. Chaque couche possède des limites, des API et des contrats de sécurité bien définis. Les flux de données circulent strictement vers le haut à travers des passerelles authentifiées et régies par des politiques.

## 2. Sous-systèmes principaux

### 2.1 Moteur d'exécution souverain
Couche d'exécution d'IA. Responsable du chargement des modèles, de l'inférence, de l'ordonnancement et de l'isolation des ressources.

### 2.2 Couche mémoire et coordination
Stockage persistant, chiffré et distribué pour les vecteurs, les caches KV et la synchronisation d'état.

### 2.3 Couche identité et sécurité
Identité Zero Trust pour les nœuds, les charges de travail et les utilisateurs.

### 2.4 Couche fédération et maillage
Communication inter-nœuds, découverte et synchronisation pour les déploiements multi-nœuds.

## 3. Profils de déploiement

| Profil | Cible | Particularité |
|--------|-------|--------------|
| Edge | Appareils ARM, IoT | Inférence CPU, local, déconnecté |
| Air-Gapped | Réseaux isolés | GPU + CPU, AES-256 + TPM, pas de WAN |
| Datacenter | Clusters GPU | Multi-GPU vLLM, base distribuée |
| Personnel | Portable, homelab | CPU/GPU, FS local, VPN optionnel |

---

*Voir la [version anglaise canonique](/ARCHITECTURE.md) pour la référence.*
