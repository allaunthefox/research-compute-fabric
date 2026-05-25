{ config, pkgs, lib, hostName, serverAddr, domain ? "researchstack.info", ... }:

let
  mailDomain = domain;
  sendAlert = pkgs.writeShellScriptBin "send-alert" ''
    set -euo pipefail
    subject="''${1:-Alert}"
    body="''${2:-No details}"
    to="''${ALERT_TO:-allaun@${mailDomain}}"
    from="''${ALERT_FROM:-allaun@${mailDomain}}"

    if [ ! -s /etc/msmtp/protonmail-password ]; then
      echo "missing /etc/msmtp/protonmail-password" >&2
      exit 1
    fi

    printf 'From: %s\nTo: %s\nSubject: %s\n\n%s\n' "$from" "$to" "$subject" "$body" \
      | ${pkgs.msmtp}/bin/msmtp -a default -- "$to"
  '';
in
{
  imports = [
    ./roles/edge.nix
  ];

  # Disk layout — matches current microvm-racknerd partition table
  boot.loader.grub.devices = lib.mkDefault [ "/dev/vda" ];
  boot.loader.grub.enable = true;
  fileSystems."/" = lib.mkDefault {
    device = "/dev/vda1";
    fsType = "ext4";
  };
  swapDevices = lib.mkDefault [ { device = "/dev/vda2"; } ];

  networking.hostName = lib.mkDefault hostName;
  networking.domain = lib.mkDefault mailDomain;

  # ── Postfix ───────────────────────────────────────────────────────────────
  services.postfix = {
    enable = true;
    hostname = "mail.${mailDomain}";
    domain = mailDomain;
    origin = mailDomain;
    destination = [ mailDomain ];
    networks = [ "127.0.0.0/8" ];

    extraConfig = ''
      mailbox_command = ${pkgs.dovecot}/libexec/dovecot/deliver
      home_mailbox = Maildir/
    '';
  };

  # ── Dovecot ───────────────────────────────────────────────────────────────
  services.dovecot2 = {
    enable = true;
    enableImap = true;
    enablePop3 = false;

    extraConfig = ''
      ssl = yes
      ssl_prefer_server_ciphers = yes
      ssl_min_protocol = TLSv1.2
      mail_location = maildir:/var/mail/%n
      auth_mechanisms = plain login
      ssl = yes
      passdb {
        driver = passwd-file
        args = /etc/dovecot/users
      }
      userdb {
        driver = static
        args = uid=5000 gid=5000 home=/var/mail/%n
      }
    '';
  };

  # Create mailbox user and directory
  users.users.postmaster = {
    isSystemUser = true;
    uid = 5000;
    group = "postmaster";
    home = "/var/mail/postmaster";
    createHome = true;
  };
  users.groups.postmaster = {
    gid = 5000;
    members = [ "postmaster" ];
  };

  # ── ProtonMail Bridge ─────────────────────────────────────────────────────
  systemd.services.protonmail-bridge = lib.mkIf (pkgs ? protonmail-bridge) {
    description = "ProtonMail Bridge SMTP relay";
    after = [ "network.target" ];
    wants = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "protonmail-bridge";
      StateDirectory = "protonmail/bridge";
      ExecStart = "${pkgs.writeShellScript "bridge-run" ''
        ${pkgs.socat}/bin/socat TCP-LISTEN:1025,fork TCP:127.0.0.1:1025 &
        ${pkgs.socat}/bin/socat TCP-LISTEN:1143,fork TCP:127.0.0.1:1143 &
        rm -f /tmp/bridge-faketty
        mkfifo /tmp/bridge-faketty
        cat /tmp/bridge-faketty | ${pkgs.protonmail-bridge}/bin/protonmail-bridge --cli
      ''}";
      Restart = "on-failure";
      RestartSec = 10;
    };
  };

  users.users.protonmail-bridge = lib.mkIf (pkgs ? protonmail-bridge) {
    isSystemUser = true;
    group = "protonmail-bridge";
    home = "/var/lib/protonmail";
    createHome = true;
  };
  users.groups.protonmail-bridge = lib.mkIf (pkgs ? protonmail-bridge) {};

  # ── ProtonMail alert relay ────────────────────────────────────────────────
  environment.etc."msmtprc".text = ''
    defaults
    auth           login
    tls            on
    tls_starttls   on
    tls_certcheck  off

    account        protonmail
    host           127.0.0.1
    port           1025
    from           allaun@${mailDomain}
    user           allaun@${mailDomain}
    passwordeval   cat /etc/msmtp/protonmail-password

    account default: protonmail
  '';
  environment.etc."msmtprc".mode = "0600";

  systemd.tmpfiles.rules = [
    "d /etc/msmtp 0700 root root -"
  ];

  environment.etc."profile.d/research-stack-alerts.sh".text = ''
    export ALERT_FROM=''${ALERT_FROM:-allaun@${mailDomain}}
    export ALERT_TO=''${ALERT_TO:-allaun@${mailDomain}}
  '';

  environment.systemPackages = with pkgs; [
    msmtp
    sendAlert
    socat
  ] ++ lib.optional (pkgs ? protonmail-bridge) pkgs.protonmail-bridge;

  # ── rs-surface ────────────────────────────────────────────────────────────
  systemd.services.rs-surface = {
    description = "Research Stack Surface Daemon";
    after = [ "network.target" "tailscaled.service" ];
    wants = [ "network.target" "tailscaled.service" ];
    wantedBy = [ "multi-user.target" ];
    environment = {
      RS_CREDENTIAL_CONFIG = "/etc/rs-surface/credentials.json";
      RS_SURFACE_PORT = "8444";
      RS_SURFACE_HOST = "0.0.0.0";
      RUST_LOG = "info";
    };
    serviceConfig = {
      Type = "simple";
      WorkingDirectory = "/opt/rs-surface";
      ExecStart = "${pkgs.bash}/bin/bash /opt/rs-surface/run.sh";
      Restart = "always";
      RestartSec = 5;
    };
  };

  # ── Caddy ─────────────────────────────────────────────────────────────────
  services.caddy = {
    enable = true;
    extraConfig = ''
      mail.${domain} { reverse_proxy 127.0.0.1:30808 }
      webmail.${domain} { reverse_proxy 127.0.0.1:30808 }
      cred.${domain} { reverse_proxy 127.0.0.1:8444 }
    '';
  };

  # ── Firewall ──────────────────────────────────────────────────────────────
  networking.firewall.allowedTCPPorts = [
    25 143 465 587 993
    1025 1143
    8444
    30808
  ];

}
