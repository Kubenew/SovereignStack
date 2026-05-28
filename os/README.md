# Sovereign Node OS

SovereignStack provides immutable, verifiable base OS images designed specifically for running the stack in air-gapped or high-security environments.

We offer two supported paths:

## 1. NixOS Flake (Appliance Mode)

The NixOS configuration (`nixos/`) provides a declarative, reproducible system built from scratch.

### Features
- **Immutability**: The root filesystem (`/`) is a `tmpfs` RAM disk. All state is lost on reboot unless explicitly persisted to `/var/lib/sovereign`.
- **Reproducibility**: Defined by `flake.nix`, ensuring exact byte-for-byte reproducibility of the OS image.
- **Pre-configured Stack**: The `sovereign-stack-module.nix` automatically bootstraps K3s, WireGuard for federation, and deploys the Helm chart.

### Usage
```bash
# Build the system closure
nix build .#nixosConfigurations.sovereign-node.config.system.build.toplevel
```

## 2. Talos Linux (Kubernetes-Native)

The Talos configurations (`talos/`) provide a minimal, hardened OS designed exclusively for running Kubernetes.

### Features
- **No SSH**: Interaction is purely via the gRPC Talos API.
- **Read-Only OS**: The entire OS runs from squashfs.
- **Air-Gapped Ready**: Configured to drop NTP and rely on hardware clocks; patches included for strict host-level firewalls.

### Usage
```bash
# Generate secrets
talosctl gen secrets -o secrets.yaml

# Apply control plane config
talosctl apply-config -i <IP> -f controlplane.yaml

# Apply worker config and network lockdown patch
talosctl apply-config -i <IP> -f worker.yaml --patch @patches/sovereign-network.yaml
```
