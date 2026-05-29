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
  };

  swapDevices = [
    { device = "/dev/vda3"; size = 65536; }
  ];

  # ── Users ─────────────────────────────────────────────────────────────────
  users.users.researcher = {
    isNormalUser = true;
    description = "Research Stack developer";
    extraGroups = [
      "wheel"
      "docker"
      "keys"
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
    # listenAddresses = [{ port = 22; }];
  };

  # ── nix-ld (run x86_64 binaries on ARM64) ────────────────────────────────
  programs.nix-ld.enable = true;

  # ── uv is installed via environment.systemPackages ──────────────────────

  # ── Lean LSP services ──────────────────────────────────────────────────────
  # Lean 4.19.0 LSP on port 8765 (streamable-http)
  systemd.services.lean-lsp-mcp = {
    description = "Lean LSP MCP server (v4.19.0)";
    after = [ "network.target" ];
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
      ];
    };
  };

  # Lean 4.30.0-rc2 LSP on port 8766 (for mathlib)
  systemd.services.lean-lsp-mathlib = {
    description = "Lean LSP MCP server (v4.30.0-rc2, mathlib)";
    after = [ "network.target" ];
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
      ];
    };
  };

  # ── Ollama model puller helper ─────────────────────────────────────────────
  # Run with: sudo -u researcher /var/lib/ollama/model-pull.sh deepseek-r1:7b
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

  # ── Docker (for x86_64 images via nix-ld) ────────────────────────────────
  virtualisation.docker = {
    enable = true;
    autoPrune.enable = true;
    enableOnBoot = true;
    # Store images on a larger disk if available
    # dataRoot = "/var/lib/docker";
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
    # Core utilities
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
  ];

  # ── Performance tuning for 64GB RAM / 18 cores ─────────────────────────────
  # Aggressive transparent hugepage for memory-heavy workloads
  boot.kernel.sysctl = {
    "vm.nr_hugepages" = 1024;
  };

  # ── Security ────────────────────────────────────────────────────────────────
  security.sudo.wheelNeedsPassword = false;

  # ── System state ────────────────────────────────────────────────────────────
  system.stateVersion = "25.11";
}
