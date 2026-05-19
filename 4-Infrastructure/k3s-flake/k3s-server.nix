{ config, pkgs, lib, hostName, serverAddr, domain, ... }:

let
  caddyWithPorkbun = pkgs.caddy.withPlugins {
    plugins = [ "github.com/caddy-dns/porkbun@v0.3.1" ];
    hash = "sha256-X11vSQRbBg25I1eSKF2O5QBRS7zGOtdGhLISiwrHclw=";
  };
in {
  ##########################################################################
  # EDIT HERE — set your domain
  # The domain below is used for TLS certificates via Porkbun DNS challenge.
  # Set PORKBUN_API_KEY and PORKBUN_SECRET_KEY in /etc/caddy/porkbun.env
  # (sops-injected via porkbun-env.age).
  ##########################################################################

  sops.secrets.porkbun-env = {
    sopsFile = ./secrets/porkbun-env.age;
    path = "/etc/caddy/porkbun.env";
  };

  sops.secrets.authentik-secrets = {
    sopsFile = ./secrets/authentik-secrets.age;
  };

  services.k3s = {
    enable = true;
    role = "server";
    clusterInit = true;
    extraFlags = [ "--disable=traefik" ];
  };

  systemd.services.caddy.serviceConfig.EnvironmentFile = [ "/etc/caddy/porkbun.env" ];

  services.caddy = {
    enable = true;
    package = caddyWithPorkbun;
    extraConfig = ''
      auth.${domain} {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        reverse_proxy 127.0.0.1:30800
      }

      status.${domain} {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        reverse_proxy 127.0.0.1:30801
      }

      apps.${domain} {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        reverse_proxy 127.0.0.1:30802
      }

      home.${domain} {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        reverse_proxy 127.0.0.1:30803
      }

      pulse.${domain} {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        reverse_proxy 127.0.0.1:30804
      }

      ${domain} {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
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
      AUTHENTIK_SECRETS = "${config.sops.secrets.authentik-secrets.path}";
    };
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      Restart = "on-failure";
      RestartSec = 10;
      ExecStart = "${./scripts/deploy-services.sh}";
    };
  };
}
