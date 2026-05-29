{ config, pkgs, lib, ... }:

{
  imports = [
    # Hardware configuration (if needed)
  ];

  # ── System identity ───────────────────────────────────────────────────────
  networking.hostName = "rs-vps";
  time.timeZone = "Europe/Berlin";

  # ── Boot ──────────────────────────────────────────────────────────────────
  boot.loader.grub.enable = lib.mkDefault true;
  boot.loader.grub.device = "/dev/vda";
  boot.loader.grub.efiSupport = true;
  boot.loader.grub.efiInstallAsRemovable = true;

  # ── Filesystems ────────────────────────────────────────────────────────────
  # NOTE: Fill in actual partition layout from CCP before deploying.
  # Run `lsblk` or `fdisk -l` after booting the NixOS installer ISO.
  fileSystems = {
    "/" = {
      device = "/dev/vda1";
      fsType = "ext4";
      autoMount = true;
    };
    "/boot/efi" = {
      device = "/dev/vda2";
      fsType = "vfat";
      autoMount = true;
    };

    # ── RAM disk for build scratch (32GB) ────────────────────────────────
    # /tmp on tmpfs: faster than disk, cleared on reboot
    "/tmp" = {
      device = "tmpfs";
      fsType = "tmpfs";
      options = [ "size=32G" "mode=1777" ];
    };

    # /run/shm for POSIX shared memory
    "/run/shm" = {
      device = "tmpfs";
      fsType = "tmpfs";
      options = [ "size=32G" ];
    };
  };

  swapDevices = [
    { device = "/dev/vda3"; size = 65536; }
  ];

  # ── Nix caching ────────────────────────────────────────────────────────────
  nix.settings = {
    # Use the global NixOS cache
    substituters = [ "https://cache.nixos.org" ];
    trusted-substituters = [ "https://cache.nixos.org" ];

    # Lean / mathlib community cache (accelerates lake builds)
    extra-substituters = [ "https://leanprover-community.github.io" ];
    extra-trusted-public-keys = [
      "leanprover-community.github.io-1:a8UP+R2uLj3/r6nGCoDSo1R4+/tJ1BLC5W3gNiV/Es="
    ];

    # Parallel downloads
    max-jobs = "auto";

    # Keep 50 generations per user profile
    keep-derivations = true;
    keep-outputs = true;
  };

  # ── Tailscale mesh networking ──────────────────────────────────────────────
  services.tailscale = {
    enable = true;
    # "server" makes this a relay node (exit node for other machines)
    useRoutingFeatures = "server";
    # Enable tailscale SSH (auth via tailnet)
    extraUpFlags = [
      "--accept-dns=false"
      "--operator=root"
    ];
  };

  # ── Users ─────────────────────────────────────────────────────────────────
  users.users.researcher = {
    isNormalUser = true;
    description = "Research Stack developer";
    extraGroups = [
      "wheel"
      "docker"
      "keys"
      "tailscale"
    ];
    openssh.authorizedKeys.keys = [
      # Add SSH keys here
    ];
  };

  # ── OpenSSH ────────────────────────────────────────────────────────────────
  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "yes";
      PasswordAuthentication = false;
    };
  };

  # ── nix-ld (run x86_64 binaries on ARM64) ────────────────────────────────
  programs.nix-ld.enable = true;

  # ── Build parallelism tunables ──────────────────────────────────────────────
  # Set by systemd service env in individual services, but also available globally
  environment.variables = {
    LAKE_JOBS = "16";
    MAKEFLAGS = "-j16";
    NIX_BUILD_CORES = "16";
    # tmpfs means /tmp is fast; pin lean packages there
    XDG_CACHE_HOME = "/home/researcher/.cache";
  };

  # ── Lean LSP services ──────────────────────────────────────────────────────
  systemd.services.lean-lsp-mcp = {
    description = "Lean LSP MCP server (v4.19.0)";
    after = [ "network.target" "tailscaled.service" ];
    wantedBy = [ "multi-user.target" ];

    script = let
      lean-lsp = pkgs.writeShellScriptBin "lean-lsp-run" ''
        #!${pkgs.bash}/bin/bash
        set -euo pipefail
        export ELAN_TOOLCHAIN=4.19.0
        export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
        export PATH="${pkgs.uv}/bin:$HOME/.elan/bin:$PATH"
        exec uv tool run --from lean-lsp-mcp lean-lsp-mcp --port 8765 --stdio
      '';
    in ''
      exec ${lean-lsp}/bin/lean-lsp-run
    '';

    serviceConfig = {
      Type = "simple";
      Restart = "always";
      RestartSec = "5s";
      User = "researcher";
      Group = "researcher";
      WorkingDirectory = "/home/researcher";
      Environment = [
        "ELAN_TOOLCHAIN=4.19.0"
        "HOME=/home/researcher"
        "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
        "LAKE_JOBS=16"
        "XDG_CACHE_HOME=/home/researcher/.cache"
      ];
    };
  };

  systemd.services.lean-lsp-mathlib = {
    description = "Lean LSP MCP server (v4.30.0-rc2, mathlib)";
    after = [ "network.target" "tailscaled.service" ];
    wantedBy = [ "multi-user.target" ];

    script = let
      lean-lsp-mathlib = pkgs.writeShellScriptBin "lean-lsp-mathlib-run" ''
        #!${pkgs.bash}/bin/bash
        set -euo pipefail
        export ELAN_TOOLCHAIN=4.30.0-rc2
        export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
        export PATH="${pkgs.uv}/bin:$HOME/.elan/bin:$PATH"
        exec uv tool run --from lean-lsp-mcp lean-lsp-mcp --port 8766 --stdio
      '';
    in ''
      exec ${lean-lsp-mathlib}/bin/lean-lsp-mathlib-run
    '';

    serviceConfig = {
      Type = "simple";
      Restart = "always";
      RestartSec = "5s";
      User = "researcher";
      Group = "researcher";
      WorkingDirectory = "/home/researcher";
      Environment = [
        "ELAN_TOOLCHAIN=4.30.0-rc2"
        "HOME=/home/researcher"
        "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
        "LAKE_JOBS=16"
        "XDG_CACHE_HOME=/home/researcher/.cache"
      ];
    };
  };

  # ── Python LSP TCP on port 8767 ──────────────────────────────────────────
  systemd.services.pylsp = {
    description = "Python LSP server (TCP)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    script = let
      pythonEnv = pkgs.python311.withPackages (ps: with ps; [
        numpy scipy sympy pandas matplotlib seaborn
        uncertainties pint
        beautifulsoup4 lxml
        requests httpx
        fastapi uvicorn pydantic
        python-dateutil
      ]);
      pylsp-script = pkgs.writeShellScriptBin "pylsp-run" ''
        #!${pkgs.bash}/bin/bash
        set -euo pipefail
        exec ${pythonEnv}/bin/python -m pylsp --host 0.0.0.0 --port 8767
      '';
    in ''
      exec ${pylsp-script}/bin/pylsp-run
    '';

    serviceConfig = {
      Type = "simple";
      Restart = "always";
      RestartSec = "5s";
      User = "researcher";
      Group = "researcher";
      WorkingDirectory = "/home/researcher";
      Environment = [
        "HOME=/home/researcher"
        "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
        "PYTHONUNBUFFERED=1"
      ];
    };
  };

  # ── Ollama inference server on port 11434 ─────────────────────────────────
  systemd.services.ollama = {
    description = "Ollama LLM inference server";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    script = ''
      #!${pkgs.bash}/bin/bash
      set -euo pipefail
      export OLLAMA_HOST=0.0.0.0:11434
      export OLLAMA_MODELS=/home/researcher/.ollama/models
      mkdir -p $OLLAMA_MODELS
      exec ${pkgs.ollama}/bin/ollama serve
    '';

    serviceConfig = {
      Type = "simple";
      Restart = "always";
      RestartSec = "5s";
      User = "researcher";
      Group = "researcher";
      WorkingDirectory = "/home/researcher";
      Environment = [
        "HOME=/home/researcher"
        "PATH=${pkgs.ollama}/bin:${pkgs.curl}/bin"
        "OLLAMA_MODELS=/home/researcher/.ollama/models"
      ];
    };
  };

  # ── Ollama model puller (oneshot) ────────────────────────────────────────
  # Usage: sudo -u researcher systemctl start ollama-model-pull@"deepseek-r1:7b"
  systemd.services.ollama-model-pull = {
    description = "Ollama model puller";
    after = [ "ollama.service" ];
    wantedBy = [ "multi-user.target" ];
    script = ''
      #!${pkgs.bash}/bin/bash
      MODEL="''${1:-deepseek-r1:7b}"
      exec ${pkgs.ollama}/bin/ollama pull "$MODEL"
    '';
    serviceConfig = {
      Type = "oneshot";
      User = "researcher";
      RemainAfterExit = true;
    };
  };

  # ── ENE database restoration (oneshot) ───────────────────────────────────
  # Copies backed-up ENE data from external disk to the VPS
  # Run manually after mounting the backup drive:
  #   sudo systemctl start ene-restore
  systemd.services.ene-restore = {
    description = "Restore ENE from backup";
    after = [ "postgresql.service" ];
    wantedBy = [ "multi-user.target" ];
    script = let
      backupDir = "/mnt/aws-backup-20260529";  # mount backup disk here first
    in ''
      #!${pkgs.bash}/bin/bash
      set -euo pipefail
      export PGHOST=/run/postgresql
      export PGDATA=/var/lib/postgresql/16/data
      export PGUSER=postgres
      export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt

      echo "Restoring ENE schema..."
      sudo -u postgres psql -c "CREATE DATABASE ene;" 2>/dev/null || true
      sudo -u postgres pg_restore -C -d postgres "${backupDir}/rds_dump/ene_schema.sql" 2>/dev/null || true

      echo "Restoring ENE data..."
      sudo -u postgres pg_restore -C -d ene "${backupDir}/rds_dump/ene_full.dump" 2>/dev/null || true

      echo "Importing CSV tables..."
      # Import CSVs (list tables that need CSV import)
      for tbl in $(ls "${backupDir}/rds_tables/"*.csv 2>/dev/null | xargs -I{} basename {} .csv); do
        echo "  Importing $tbl..."
        sudo -u postgres psql -d ene -c "\\COPY $tbl FROM '${backupDir}/rds_tables/$tbl.csv' WITH (FORMAT csv, HEADER true)" 2>/dev/null || true
      done

      echo "ENE restore complete."
    '';
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
  };

  # ── Docker (for x86_64 images via nix-ld) ────────────────────────────────
  virtualisation.docker = {
    enable = true;
    autoPrune.enable = true;
    enableOnBoot = true;
  };

  # ── Networking ─────────────────────────────────────────────────────────────
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [
      22    # SSH
      80    # HTTP
      443   # HTTPS
      8765  # Lean LSP (v4.19.0)
      8766  # Lean LSP (v4.30.0-rc2)
      8767  # Python LSP
      11434 # Ollama
    ];
    allowedUDPPorts = [ ];
  };

  # ── Packages ────────────────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    git git-lfs
    bash bashInteractive coreutils findutils gnugrep gnused gawk
    util-linux
    curl wget rsync zstd xz gnutar gzip
    ripgrep jq
    gnumake
    nodejs_22
    uv
    elan
    texliveFull
    gnuplot maxima octave
    typst
    openssh cacert
    less which file procps htop
    glibc binutils
    openssl pkg-config
    graphviz
    postgresql_16
    docker containerd
    tailscale  # mesh networking
  ];

  # ── Performance tuning for 64GB RAM / 18 cores ────────────────────────────
  boot.kernel.sysctl = {
    # Transparent hugepage support for memory-intensive workloads
    "vm.nr_hugepages" = 1024;
    # Swappiness: prefer RAM over swap for build workloads
    "vm.swappiness" = 10;
  };

  # ── Security ────────────────────────────────────────────────────────────────
  security.sudo.wheelNeedsPassword = false;

  # ── System state ────────────────────────────────────────────────────────────
  system.stateVersion = "25.11";
}
