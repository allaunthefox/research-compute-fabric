{ config, pkgs, lib, hostName, serverAddr, domain, ... }:

{
  ##########################################################################
  # EDIT HERE — set your domain
  # The domain below is used for TLS certificates via Porkbun DNS challenge.
  # Set PORKBUN_API_KEY and PORKBUN_SECRET_KEY in /etc/caddy/porkbun.env
  # (sops-injected via porkbun-env.age).
  ##########################################################################

  sops.secrets.porkbun-env = {
    sopsFile = ./secrets/porkbun-env.age;
    format = "yaml";
    path = "/etc/caddy/porkbun.env";
  };

  sops.secrets.authentik-secrets = {
    sopsFile = ./secrets/authentik-secrets.age;
    format = "yaml";
  };

  services.k3s = {
    enable = true;
    role = "server";
    clusterInit = true;
    extraFlags = [
      "--disable=traefik"
      "--tls-san=100.102.173.61"
      "--tls-san=researchstack.info"
      "--tls-san=nixos-laptop"
      "--advertise-address=100.102.173.61"
      "--node-ip=100.102.173.61"
      "--flannel-iface=tailscale0"
    ];
  };

  systemd.services.caddy.serviceConfig.EnvironmentFile = [ "/etc/caddy/porkbun.env" ];

  services.caddy = {
    enable = true;
    package = pkgs.caddy;
    globalConfig = ''
      auto_https off
    '';
    extraConfig = ''
      http://auth.${domain} {
        reverse_proxy 100.85.244.73:30080
      }

      http://status.${domain} {
        reverse_proxy 127.0.0.1:30801
      }

      http://apps.${domain} {
        reverse_proxy 127.0.0.1:30802
      }

      http://home.${domain} {
        reverse_proxy 127.0.0.1:30803
      }

      http://pulse.${domain} {
        reverse_proxy 127.0.0.1:30804
      }

      http://dash.${domain} {
        reverse_proxy 127.0.0.1:30805
      }

      http://media.${domain} {
        reverse_proxy 127.0.0.1:30810
      }

      http://vault.${domain} {
        reverse_proxy 10.43.130.188:80
      }

      http://books.${domain} {
        reverse_proxy 127.0.0.1:30807
      }

      http://music.${domain} {
        reverse_proxy 127.0.0.1:30809
      }

      http://mail.${domain} {
        reverse_proxy 127.0.0.1:30808
      }

      http://webmail.${domain} {
        reverse_proxy 127.0.0.1:30808
      }

      http://${domain} {
        respond "k3s unified topology — Research Stack"
      }
    '';
  };

  systemd.services.deploy-k3s-services = {
    description = "Deploy k3s topology services";
    after = [ "k3s.service" "tailscaled.service" "network-online.target" ];
    wants = [ "k3s.service" "tailscaled.service" "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ kubectl ];
    environment = {
      KUBECONFIG = "/etc/rancher/k3s/k3s.yaml";
      AUTHENTIK_SECRETS = "${config.sops.secrets.authentik-secrets.path}";
    };
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      Restart = "on-failure";
      RestartSec = 10;
      ExecStart = "${pkgs.bash}/bin/bash ${./scripts/deploy-services.sh}";
    };
  };
}
