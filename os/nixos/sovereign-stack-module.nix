{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.sovereignStack;
in {
  options.services.sovereignStack = {
    enable = mkEnableOption "SovereignStack Core Services";

    nodeId = mkOption {
      type = types.str;
      default = "sovereign-node-${config.networking.hostName}";
      description = "Unique ID for this node in the Sovereign mesh.";
    };

    complianceLevel = mkOption {
      type = types.enum [ "STRICT" "DEVELOPMENT" ];
      default = "STRICT";
      description = "OASA compliance enforcement level.";
    };

    federation = {
      enable = mkEnableOption "Enable Sovereign Mesh Federation (WireGuard)";
      peers = mkOption {
        type = types.listOf types.str;
        default = [];
        description = "List of peer public keys / endpoints for WireGuard.";
      };
    };
  };

  config = mkIf cfg.enable {
    # 1. WireGuard Mesh for Federation (RFC 0004)
    networking.wireguard.interfaces = mkIf cfg.federation.enable {
      wg-sovereign = {
        ips = [ "10.100.0.1/24" ];
        listenPort = 51901;
        privateKeyFile = "/var/lib/sovereign/secrets/wg-private.key";
        # Peers would be mapped from cfg.federation.peers
      };
    };

    # 2. Kubernetes Node Labels
    services.k3s.extraFlags = "--node-label sovereignstack.ai/node-id=${cfg.nodeId} --node-label sovereignstack.ai/compliance=${cfg.complianceLevel}";

    # 3. Apply the SovereignStack helm chart on K3s startup
    systemd.services.deploy-sovereign-stack = {
      description = "Deploy SovereignStack Helm Chart";
      after = [ "k3s.service" ];
      wants = [ "k3s.service" ];
      wantedBy = [ "multi-user.target" ];
      
      script = ''
        export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
        # Wait for k3s API
        until ${pkgs.kubectl}/bin/kubectl get nodes; do sleep 5; done
        
        # Deploy the chart (assuming chart is copied to /opt/sovereignstack)
        # ${pkgs.kubernetes-helm}/bin/helm upgrade --install sovereignstack /opt/sovereignstack/charts/sovereignstack -n sovereign-stack --create-namespace
      '';
      
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
      };
    };
  };
}
