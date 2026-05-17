{ config, pkgs, lib, ... }:

let
  caddyWithPorkbun = pkgs.caddy.withPlugins {
    plugins = [ "github.com/caddy-dns/porkbun@v0.3.1" ];
    hash = "sha256-X11vSQRbBg25I1eSKF2O5QBRS7zGOtdGhLISiwrHclw=";
  };
in
{
  imports = [ ./hardware-configuration.nix ];

  boot.loader.grub.enable = false;
  boot.loader.generic-extlinux-compatible.enable = true;

  networking.hostName = "cupfox";
  networking.networkmanager.enable = true;
  networking.nameservers = [ "1.1.1.1" "8.8.8.8" ];
  networking.networkmanager.dns = "none";
  networking.networkmanager.settings.main."rc-manager" = "unmanaged";

  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    auto-optimise-store = true;
  };
  systemd.services.nix-daemon.serviceConfig.BindReadOnlyPaths = [ "/etc/resolv.conf" ];

  time.timeZone = "America/Chicago";

  users.users.root.openssh.authorizedKeys.keys = [
    "ssh-ed25519 AAAAC3NzaC1lZGEyNTU5AAAAL1RhaWxzY2FsZSBkZXZpY2U6IGNhbiB5b3UgcmVhZCB0aGlzPw== root@cupfox"
  ];

  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "prohibit-password";
      PasswordAuthentication = false;
    };
  };

  services.tailscale.enable = true;

  systemd.services.caddy.serviceConfig.EnvironmentFile = [ "/etc/caddy/porkbun.env" ];

  services.caddy = {
    enable = true;
    logFormat = "level INFO";
    package = caddyWithPorkbun;
    extraConfig = ''
      researchstack.info, cupfox.researchstack.info, http://100.126.151.57 {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        root * /var/www/researchstack
        file_server
      }

      ollama.researchstack.info {
        tls {
          dns porkbun {
            api_key {$PORKBUN_API_KEY}
            api_secret_key {$PORKBUN_SECRET_KEY}
          }
        }
        reverse_proxy http://100.101.198.87:11434
      }

      cupfox.tail4e7094.ts.net {
        tls internal

        handle_path /ollama/* {
          reverse_proxy http://100.101.198.87:11434
        }

        handle {
          respond "cupfox orchestration node"
        }
      }
    '';
  };

  virtualisation.podman = {
    enable = true;
    defaultNetwork.settings.dns_enabled = true;
  };
  virtualisation.containers.enable = true;

  virtualisation.oci-containers = {
    backend = "podman";
    containers = {
      research-stack = {
        image = "localhost/research-stack:latest";
        autoStart = true;
        cmd = [ "sleep" "infinity" ];
        extraOptions = [
          "--dns" "100.101.247.127"
          "--dns" "1.1.1.1"
          "--dns" "8.8.8.8"
        ];
      };
    };
  };

  systemd.services.laptop-1-health = {
    description = "Poll laptop-1 health via Ollama API";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.curl}/bin/curl -sf --max-time 5 http://100.101.198.87:11434/api/tags";
    };
  };

  systemd.timers.laptop-1-health = {
    description = "Poll laptop-1 health every 5 minutes";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "*:0/5";
      Persistent = true;
      RandomizedDelaySec = 30;
    };
  };

  systemd.services.microvm-health = {
    description = "Poll MicroVM-Racknerd health endpoint";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.curl}/bin/curl -sf --max-time 5 http://100.101.247.127:8443/index.sh";
    };
  };

  systemd.timers.microvm-health = {
    description = "Poll MicroVM health every 5 minutes";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "*:0/5";
      Persistent = true;
      RandomizedDelaySec = 30;
    };
  };

  environment.systemPackages = with pkgs; [
    curl
    dig
    dnsutils
    git
    htop
    jq
    podman-compose
    podman-tui
    ripgrep
    vim
    wget
  ];

  system.stateVersion = "25.05";
}
