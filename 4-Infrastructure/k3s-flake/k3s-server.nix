{ config, pkgs, lib, hostName, serverAddr, domain, ... }:

{
  ##########################################################################
  # k3s-server.nix — NixOS storage + k3s agent node
  #
  # THIS NODE IS NOT THE CONTROL PLANE.
  # The actual control plane is on cupfox (100.110.163.82).
  # This node was originally the standalone server but was migrated to
  # agent mode when cupfox was promoted to control-plane.
  #
  # Architecture:
  #   cupfox (Debian, control-plane) ← migrated from nixos
  #   nixos (NixOS, storage agent)
  #   qfox-1 (CachyOS, foxtop agent)
  #   steamdeck (NixOS, GPU agent)
  #   racknerd (Debian, edge agent + Caddy TLS)
  #   neon-64gb (Debian, ARM64 agent)
  #
  # Servicerouter (to be deployed):
  #   Edge Caddy (racknerd:443) → Tailscale → host Caddy → Traefik → Services
  ##########################################################################

  sops.secrets.k3s-token = {
    sopsFile = ./secrets/k3s-token.age;
    format = "yaml";
  };

  systemd.services.k3s.serviceConfig.EnvironmentFile = [
    config.sops.secrets.k3s-token.path
  ];

  services.k3s = {
    enable = true;
    role = "agent";
    serverAddr = "https://100.110.163.82:6443"; # cupfox control-plane
    tokenFile = config.sops.secrets.k3s-token.path;
    extraFlags = [
      "--node-ip=100.102.173.61"
      "--node-external-ip=100.102.173.61"
      "--flannel-iface=tailscale0"
      "--node-label=topology.researchstack.io/role=storage"
      "--node-label=topology.researchstack.io/gpu=false"
      "--node-label=topology.researchstack.io/storage-tier=nvme-ssd"
    ];
  };

  networking.firewall.allowedTCPPorts = [ 80 ];

  services.tailscale.enable = true;
}
