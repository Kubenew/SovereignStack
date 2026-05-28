{ config, pkgs, ... }:

{
  imports = [
    # Include the hardware scan results
    ./hardware-configuration.nix
  ];

  # Bootloader and TPM/SecureBoot
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.kernelParams = [ "intel_iommu=on" "iommu=pt" "module_blacklist=nouveau" ];

  # Immutable root filesystem (ephemeral)
  fileSystems."/" = {
    device = "tmpfs";
    fsType = "tmpfs";
    options = [ "defaults" "size=2G" "mode=755" ];
  };

  # Persistent state mounted via disko
  fileSystems."/nix" = {
    device = "/dev/disk/by-label/nixos";
    fsType = "ext4";
  };

  fileSystems."/var/lib/sovereign" = {
    device = "/dev/mapper/sovereign-data";
    fsType = "ext4";
    # Requires TPM-bound LUKS unlock
  };

  # Networking & Air-Gap Firewall
  networking.hostName = "sovereign-node";
  networking.useDHCP = true;
  
  networking.firewall = {
    enable = true;
    # Default drop all egress (Air-Gapped by default)
    # The sovereign-stack module will selectively open WireGuard
    allowPing = false;
  };

  # NVIDIA / Hardware acceleration
  hardware.opengl.enable = true;
  services.xserver.videoDrivers = [ "nvidia" ];
  hardware.nvidia = {
    modesetting.enable = true;
    open = false;
    nvidiaSettings = false;
    package = config.boot.kernelPackages.nvidiaPackages.production;
  };

  # Container Runtime (K3s)
  services.k3s = {
    enable = true;
    role = "server";
    extraFlags = "--disable traefik --flannel-backend=host-gw";
  };

  # System packages
  environment.systemPackages = with pkgs; [
    git
    vim
    wget
    k3s
    pciutils
    tpm2-tools
  ];

  # Hardening
  security.tpm2.enable = true;
  security.tpm2.pkcs11.enable = true;
  
  services.openssh = {
    enable = true;
    settings.PasswordAuthentication = false;
    settings.PermitRootLogin = "prohibit-password";
  };

  system.stateVersion = "24.05";
}
