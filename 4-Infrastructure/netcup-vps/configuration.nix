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
      "docker"      # podman docker compat socket
      "k3s"        # k3s API access
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

  # ── PostgreSQL (ENE database) ───────────────────────────────────────────────
  services.postgresql = {
    enable = true;
    package = pkgs.postgresql_16;
    # Enable JIT for analytical queries on ENE data
    settings.jit = "on";
    # Memory tuning for 64GB RAM
    settings.shared_buffers = "16GB";
    settings.effective_cache_size = "48GB";
    settings.work_mem = "256MB";
    settings.maintenance_work_mem = "2GB";
    settings.effective_io_concurrency = 200;
    settings.max_worker_processes = "16";
    # Enable parallel query execution
    settings.max_parallel_workers_per_gather = "8";
    settings.max_parallel_workers = "16";
    # Logging
    settings.log_destination = "stderr";
    settings.log_line_prefix = "ene %p %u@%d ";
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

      echo "Creating ENE database..."
      sudo -u postgres psql -c "CREATE DATABASE ene;" 2>/dev/null || true

      echo "Restoring ENE schema..."
      sudo -u postgres psql -d ene -f "${backupDir}/rds_dump/ene_schema.sql" 2>/dev/null || true

      echo "Restoring ENE data..."
      sudo -u postgres pg_restore -d ene "${backupDir}/rds_dump/ene_full.dump" 2>/dev/null || true

      echo "Importing CSV tables..."
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

  # ── Caddy reverse proxy (HTTPS for LSP endpoints) ──────────────────────────
  # Certificates via Let's Encrypt / Caddy DNS challenge (configure domain first)
  services.caddy = {
    enable = true;
    virtualHosts = {
      # TLS will work once a domain points to this VPS
      # "rs-vps.example.com" = {
      #   extraConfig = ''
      #     reverse_proxy /lean* localhost:8765
      #     reverse_proxy /python* localhost:8767
      #     reverse_proxy /ollama* localhost:11434
      #     reverse_proxy localhost:8096
      #   '';
      # };
    };
    globalConfig = ''
      admin off
      auto_https off
    '';
  };

  # ── Jellyfin media server (port 8096) ────────────────────────────────────
  # Stream video, audio, and images to any device.
  # Transcoding via jellyfin-ffmpeg (VA-API/QSV/OCL on x86, software on ARM64).
  systemd.services.jellyfin = {
    description = "Jellyfin media server";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    script = ''
      #!${pkgs.bash}/bin/bash
      set -euo pipefail
      export JELLYFIN_DATA_DIR=/home/researcher/.local/share/jellyfin
      export JELLYFIN_CONFIG_DIR=/home/researcher/.config/jellyfin
      export JELLYFIN_LOG_DIR=/home/researcher/.local/log/jellyfin
      export JELLYFIN_CACHE_DIR=/home/researcher/.cache/jellyfin
      mkdir -p $JELLYFIN_DATA_DIR $JELLYFIN_CONFIG_DIR $JELLYFIN_LOG_DIR $JELLYFIN_CACHE_DIR
      exec ${pkgs.jellyfin}/bin/jellyfin \
        --datadir "$JELLYFIN_DATA_DIR" \
        --configdir "$JELLYFIN_CONFIG_DIR" \
        --logdir "$JELLYFIN_LOG_DIR" \
        --cachedir "$JELLYFIN_CACHE_DIR" \
        --ffmpeg ${pkgs.jellyfin-ffmpeg}/bin/ffmpeg \
        --webdir ${pkgs.jellyfin-web}/share/jellyfin-web
    '';

    serviceConfig = {
      Type = "simple";
      Restart = "always";
      RestartSec = "10s";
      User = "researcher";
      Group = "researcher";
      Environment = [
        "HOME=/home/researcher"
        "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
      ];
    };
  };

  # ── Prometheus node exporter (port 9100) ──────────────────────────────────
  # Exposes hardware/OS metrics for monitoring (Uptime Kuma, etc.)
  services.prometheus.exporters = {
    node = {
      enable = true;
      port = 9100;
      enabledCollectors = [ "systemd" "logind" ];
      # Don't firewall this — only expose on internal interfaces
      openFirewall = false;
    };
  };

  # ── Automatic NixOS upgrades (weekly) ───────────────────────────────────
  systemd.timers.nix-upgrade = {
    wantedBy = [ "timers.target" ];
    timerConfig.OnCalendar = "weekly";
    persistent = true;
  };
  systemd.services.nix-upgrade = {
    description = "NixOS channel upgrade";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.nix}/bin/nix-channel --update nixos";
      User = "root";
    };
  };

  # ── Health check watchdog ────────────────────────────────────────────────
  # Restarts LSP/Ollama if they become unresponsive
  systemd.services.health-check = {
    description = "LSP and Ollama health watchdog";
    after = [
      "lean-lsp-mcp.service"
      "lean-lsp-mathlib.service"
      "pylsp.service"
      "ollama.service"
    ];
    wantedBy = [ "multi-user.target" ];
    script = ''
      #!${pkgs.bash}/bin/bash
      set -euo pipefail

      check_service() {
        local name="$1"; shift
        local url="$1"; shift
        if ! curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
          echo "[health] $name unhealthy at $url — restarting..."
          systemctl restart "$name"
        fi
      }

      # Lean LSP (streamable-http health check via --timeout flag)
      # check_service lean-lsp-mcp http://localhost:8765/health 2>/dev/null || true
      # Python LSP has no built-in health endpoint — check port
      if ! nc -z localhost 8767 2>/dev/null; then
        echo "[health] pylsp port 8767 not listening — restarting..."
        systemctl restart pylsp
      fi
      # Ollama API
      if ! curl -sf --max-time 5 http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "[health] ollama unhealthy — restarting..."
        systemctl restart ollama
      fi
    '';
    serviceConfig = {
      Type = "oneshot";
      # Run every 5 minutes
    };
  };
  systemd.timers.health-check = {
    wantedBy = [ "timers.target" ];
    timerConfig.OnCalendar = "*-*-* *:0/5:00";
    persistent = true;
    randomizedDelaySec = 30;
  };

  # ── Podman (container runtime) ───────────────────────────────────────────────
  # Replaces Docker; manages containers without a daemon
  virtualisation.podman = {
    enable = true;
    # Docker-compatible socket for tools that expect Docker
    dockerCompat = true;
    defaultLocks = "/var/lib/containers.lock";
    storage.settings = {
      # Use the 2TB disk for container storage
      storage.rootlessStoragePath = "/var/lib/containers";
    };
  };

  # ── k3s (lightweight Kubernetes) ─────────────────────────────────────────
  # Single-node k3s for orchestrating long-running compute workloads
  services.k3s = {
    enable = true;
    # Token and certs for node authentication
    # token = "changeme";  # Set a secure token
    # Master role only (no agents)
    role = "server";
    # Disable traefik (we have Caddy for ingress)
    disableAgent = true;
    # Extra args for the server
    extraFlags = [
      "--disable traefik"
      "--disable servicelb"
      "--disable metrics-server"
      "--write-kubeconfig-mode 0644"
    ];
    # Port config
    port = 6443;
  };

  # ── Networking ─────────────────────────────────────────────────────────────
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [
      22    # SSH
      80    # HTTP (Caddy)
      443   # HTTPS (Caddy)
      6443  # k3s Kubernetes API
      2379  # etcd client
      2380  # etcd peer
      8096  # Jellyfin media server
      8765  # Lean LSP (v4.19.0)
      8766  # Lean LSP (v4.30.0-rc2)
      8767  # Python LSP
      8920  # Jellyfin-alt HTTP
      9100  # Prometheus node exporter
      11434 # Ollama
    ];
    allowedUDPPorts = [
      1900  # Jellyfin discovery (SSDP)
    ];
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
    podman
    tailscale  # mesh networking
    netcat-openbsd  # for health check port probing

    # ── ARM64-optimized HPC / math packages ───────────────────────────
    openblas              # Multi-threaded BLAS, ARM64 Neoverse-optimized
    blis                  # Fast BLIS on ARM64
    lapack
    petsc                 # Scientific computing (sparse/direct solvers)
    slepc                 # Eigenvalue solver (PETSc-based)
    flintqs               # Fast FLINT (factorization, primality)
    pari                   # PARI/GP (number theory)
    gap                    # Groups, Algorithms, Programming
    singular              # Polynomial algebra, Gröbner bases
    symengine             # Fast C++ symbolic (SymPy backend)
    fftw                  # FFT (single/double precision)
    suitesparse           # CHOLMOD, UMFPACK, SPQR
    z3                    # SMT solver
    julia_11              # Julia 1.11 (good ARM64 SIMD)

    # ── Audio / video processing (DSP volunteer computing) ─────────────────
    ffmpeg                # Core: transcoding, streaming, filtering
    ffmpeg-full          # Full build with all filters/codecs
    flac                  # Free Lossless Audio Codec
    opus                  # Opus audio codec
    libvpx               # VP8/VP9 video codec
    libaom               # AV1 codec
    dav1d                 # AV1 decoder (fast, ASM-optimized)
    mediainfo             # Inspect audio/video metadata
    sox                   # Sound exchange — audio processing CLI
    portaudio             # Cross-platform audio I/O
    libsndfile            # Audio file I/O
    alsa-lib             # ALSA audio library

    # ── Jellyfin media server ───────────────────────────────────────────────
    jellyfin              # Media server (TV, movies, music)
    jellyfin-ffmpeg       # Jellyfin's patched FFmpeg with hardware encoding
    jellyfin-web          # Web UI
    # Hardware acceleration (common for ARM64 media)
    openssl              # Already present; TLS for jellyfin
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
