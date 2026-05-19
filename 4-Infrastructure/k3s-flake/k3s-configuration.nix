{ config, pkgs, lib, hostName, serverAddr, domain, ... }:

{
  ##########################################################################
  # EDIT HERE — fill in hostName, serverAddr, and domain
  # hostName must be set for every node.
  # serverAddr is required for agent nodes. domain is required for the server.
  #
  # Bootstrap workflow:
  #   1. Pre-generate a k3s token: openssl rand -hex 32
  #   2. Encrypt it with age as secrets/k3s-token.age
  #      (format: K3S_TOKEN=<token>)
  #   3. Deploy the server first. If no K3S_TOKEN is set, k3s auto-generates.
  #   4. For agents, set the token from step 1.
  ##########################################################################

  sops.secrets.k3s-token = {
    sopsFile = ./secrets/k3s-token.age;
  };

  systemd.services.k3s.serviceConfig.EnvironmentFile = [
    config.sops.secrets.k3s-token.path
  ];

  networking.hostName = lib.mkDefault hostName;
  networking.networkmanager.enable = true;
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];

  time.timeZone = "UTC";

  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    auto-optimise-store = true;
  };
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 7d";
  };

  users.users.root.openssh.authorizedKeys.keys = [
    # add your SSH public key(s) here
  ];

  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "prohibit-password";
      PasswordAuthentication = false;
    };
  };

  services.tailscale.enable = true;

  networking.firewall = {
    enable = true;
    allowedTCPPorts = [ 22 6443 ];
    trustedInterfaces = [ "tailscale0" ];
    allowedUDPPorts = [ 51820 ];
  };

  environment.systemPackages = with pkgs; [
    curl
    git
    htop
    jq
    k3s
    kubectl
    ripgrep
    tailscale
    vim
    wget
  ];

  system.stateVersion = "25.05";
}
