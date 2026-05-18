{ config, pkgs, ... }:
{
  imports = [ <nixpkgs/nixos/modules/virtualisation/amazon-image.nix> ];

  networking.hostName = "aws-nixos-node-1";
  networking.firewall.allowedTCPPorts = [ 80 443 ];

  documentation.enable = false;
  documentation.nixos.enable = false;
  documentation.man.enable = false;
  documentation.info.enable = false;
  documentation.doc.enable = false;

  nix.settings.auto-optimise-store = true;
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 7d";
  };

  environment.systemPackages = with pkgs; [ tailscale python3 ];

  services.tailscale.enable = true;
  services.tailscale.authKeyFile = "/etc/tailscale-auth.key";
  services.tailscale.extraUpFlags = [ "--ssh" ];

  virtualisation.podman.enable = true;

  virtualisation.oci-containers = {
    backend = "podman";
    containers = {
      heimdall = {
        image = "lscr.io/linuxserver/heimdall:latest";
        autoStart = true;
        ports = [ "127.0.0.1:8090:80" ];
        volumes = [ "/var/lib/heimdall:/config" ];
        environment = {
          PUID = "1000";
          PGID = "1000";
          TZ = "America/Chicago";
        };
      };
      forgejo = {
        image = "codeberg.org/forgejo/forgejo:1.21";
        autoStart = true;
        ports = [
          "0.0.0.0:3000:3000"
        ];
        volumes = [
          "/var/lib/forgejo/data:/data"
        ];
        environment = {
          USER_UID = "1000";
          USER_GID = "1000";
          FORGEJO__server__DOMAIN = "researchstack.info";
          FORGEJO__server__ROOT_URL = "https://researchstack.info/git/";
          FORGEJO__server__HTTP_PORT = "3000";
          FORGEJO__server__SSH_PORT = "22";
        };
      };
    };
  };

  services.caddy = {
    enable = true;
    extraConfig = ''
      researchstack.info {
        handle_path /api/* {
          reverse_proxy localhost:8444
        }
        handle_path /git/* {
          reverse_proxy localhost:3000
        }
        handle_path /appflowy/* {
          reverse_proxy localhost:8000
        }
        handle {
          basic_auth {
            admin $2b$12$yUaZ1sxezq84rRDQ3Fa48OdTx52vU7bldIfmav4cwsRn227pFJQDq
          }
          reverse_proxy localhost:8090
        }
      }

# git.researchstack.info subdomain removed - use /git/* path instead
    '';
  };

  systemd.services.rs-credential-server = {
    description = "Research Stack Credential Server";
    after = [ "network-online.target" "tailscaled.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/opt/rs-surface";
      ExecStart = "${pkgs.python3}/bin/python3 /opt/rs-surface/credential_server.py --port 8444 --bind 127.0.0.1";
      Restart = "always";
      RestartSec = "5";
      Environment = [
        "RS_CREDENTIAL_CONFIG=/etc/rs-surface/credentials.json"
        "RS_CREDENTIAL_SERVER=http://100.101.247.127:8444"
        "RS_SURFACE_NODE_ID=aws-nixos-node-1"
      ];
    };
  };


  systemd.services.appflowy-cloud = {
    description = "AppFlowy Cloud podman-compose stack";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ podman podman-compose ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      WorkingDirectory = "/var/lib/AppFlowy-Cloud";
      ExecStart = "${pkgs.podman-compose}/bin/podman-compose -f docker-compose.minimal.yml up -d";
      ExecStop = "${pkgs.podman-compose}/bin/podman-compose -f docker-compose.minimal.yml down";
    };
  };

  systemd.services.appflowy-backup = {
    description = "Daily AppFlowy PostgreSQL backup";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    path = with pkgs; [ podman ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "/var/lib/scripts/backup-appflowy-db.sh";
    };
  };

  systemd.timers.appflowy-backup = {
    description = "Daily AppFlowy backup timer";
    requires = [ "appflowy-backup.service" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
    };
    wantedBy = [ "timers.target" ];
  };
}
