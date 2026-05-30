{
  description = "Research Stack — netcup VPS (Ampere ARM64, 64GB RAM)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs, nixpkgs-stable }:
    let
      system = "aarch64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = false;
      };

      # ── Lean 4 toolchains via elan ─────────────────────────────────────────
      # elan-lsp overlays lean4 onto PATH for a given toolchain.
      # Multiple toolchains can coexist; default is set via ELAN_TOOLCHAIN.
      elan-lsp = { toolchain ? "4.19.0", port ? 8765 }:
        let
          elan-init = pkgs.runCommand "elan-init-${toolchain}" {
            nativeBuildInputs = [ pkgs.curl ];
            SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          } ''
            mkdir -p $out/etc/profile.d
            cat > $out/etc/profile.d/elan-${toolchain}.sh << 'PROFILE'
            export ELAN_TOOLCHAIN=${toolchain}
            export PATH="$HOME/.elan/toolchains/lean4-${toolchain}/bin:$PATH"
            PROFILE
          '';
        in pkgs.writeShellScriptBin "lean-lsp-mcp" ''
          #! ${pkgs.bash}/bin/bash
          set -euo pipefail
          export ELAN_TOOLCHAIN=${toolchain}
          export PATH="$HOME/.elan/toolchains/lean4-${toolchain}/bin:$PATH"
          export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
          exec uvx lean-lsp-mcp --port=${toString port} --stdio
        '';

      # ── Python LSP server ─────────────────────────────────────────────────
      pylsp-tcp = { port ? 8767, extras ? [ "all" ] }:
        let
          pythonEnv = pkgs.python311.withPackages (ps: with ps; [
            numpy scipy sympy pandas matplotlib seaborn
            uncertainties pint
            beautifulsoup4 lxml
            requests httpx
            fastapi uvicorn pydantic
            python-dateutil
          ]);
        in pkgs.writeShellScriptBin "pylsp-tcp" ''
          #! ${pkgs.bash}/bin/bash
          set -euo pipefail
          exec ${pythonEnv}/bin/python -m pylsp --host 0.0.0.0 --port ${toString port}
        '';

      # ── Ollama for inference ─────────────────────────────────────────────
      ollama-service = pkgs.writeShellScriptBin "ollama-service" ''
        #! ${pkgs.bash}/bin/bash
        set -euo pipefail
        export OLLAMA_HOST=0.0.0.0:11434
        exec ${pkgs.ollama}/bin/ollama serve
      '';

      # ── Core packages ─────────────────────────────────────────────────────
      corePackages = with pkgs; [
        # Version control
        git git-lfs
        # Shells & core utils
        bash bashInteractive coreutils findutils gnugrep gnused gawk
        util-linux
        # File transfer & compression
        curl wget rsync zstd xz gnutar gzip
        # Search & text processing
        ripgrep jq
        # Build essentials
        gnumake
        # Node (for any JS tooling)
        nodejs_22
        # Python: uv for runtime package management
        uv
        # Elan for Lean 4 toolchains
        elan
        # LaTeX
        texliveFull
        # Math CLI tools
        gnuplot maxima wxmaxima octave
        # Typesetting
        typst
        # Network / TLS
        openssh cacert
        # Shell helpers
        less which file procps htop
        # glibc / binutils
        glibc binutils
        # SSL / crypto
        openssl pkg-config
        # Graphviz
        graphviz
        # PostgreSQL client
        postgresql_16
        # Podman container runtime (Docker-compatible)
        podman
        # nix-ld for running x86_64 binaries on ARM64
        (import nixpkgs-stable {
          system = "x86_64-linux";
          config.allowUnfree = false;
        }).nix-ld
      ];

      # ── ARM64-optimized HPC / math packages ────────────────────────────────
      # Key insight: ARM64 Neoverse N1 (Ampere Altra) has excellent SIMD
      # (ARMv8.2-A SVE/SVE2), strong memory bandwidth, and cache hierarchy
      # similar to AMD Zen. These packages are built with ARM64 in mind.
      mathPackages = with pkgs; [
        # ── Linear algebra (BLAS/LAPACK ecosystem) ───────────────────────
        openblas              # Multi-threaded, ARM64 Neoverse-optimized BLAS
        blis                  # BLIS — fast on ARM64, cleaner than OpenBLAS
        lapack                # Reference LAPACK (used via OpenBLAS/BLIS backends)
        python311Packages.scipy  # Uses OpenBLAS by default

        # ── Sparse / iterative solvers ────────────────────────────────────
        petsc                 # Portable, extensible Toolkit for Scientific Computing
        slepc                 # Eigenvalue solver (builds on PETSc)

        # ── Number theory / algebra ───────────────────────────────────────
        flintqs               # Fast multi-method FLINT for factoring, primality
        pari                  # PARI/GP — number theory, algebraic number theory
        gap                   # Groups, Algorithms, Programming — computational algebra
        singular              # Polynomial computation, Gröbner bases

        # ── Fast symbolic engine (C++ backend for SymPy) ──────────────────
        symengine             # Fast C++ symbolic library; sympy can use it as backend

        # ── FFT / signal processing ─────────────────────────────────────
        fftw                  # Fast Fourier Transform (single precision)
        fftwDouble            # Double precision FFTW (separate package)

        # ── Audio / video processing (DSP volunteer computing) ─────────
        ffmpeg                # Core: transcoding, streaming, filtering
        ffmpeg-full          # Full build with all filters/codecs
        flac                  # Free Lossless Audio Codec
        opus                  # Opus audio codec
        libvpx               # VP8/VP9 video codec
        libaom               # AV1 codec
        dav1d                 # AV1 decoder
        mediainfo             # Inspect audio/video metadata
        sox                   # Sound exchange — audio processing CLI
        portaudio             # Cross-platform audio I/O
        libsndfile            # Audio file I/O
        alsa-lib             # ALSA audio library

        # ── Jellyfin media server ─────────────────────────────────────────
        jellyfin              # Media server
        jellyfin-ffmpeg      # Jellyfin's patched FFmpeg (VA-API, QSV, OCL support)
        jellyfin-web         # Web UI

        # ── BTRFS filesystem tools ───────────────────────────────────────
        btrfs-progs          # mkfs, subvolume, send/receive, scrub, balance
        btrfs-heatmap        # Visualize BTRFS space usage
        btrfs-static         # Static binaries for rescue
      ];

      # ── Python packages (full science stack) ──────────────────────────────
      pythonPackages = with pkgs.python311Packages; [
        numpy scipy sympy pandas matplotlib seaborn
        uncertainties pint
        beautifulsoup4 lxml
        requests httpx
        fastapi uvicorn pydantic
        python-dotenv pyyaml rich
        python-dateutil urllib3
        boto3 botocore
        psycopg2
        biopython networkx
        pycryptodome
        zstandard
        z3
        pywavelets
        polars
        scikit-learn
        notion-client
        pytest
        reedsolo
        cryptography
      ];

      # ── Custom etc for researcher user ───────────────────────────────────
      customEtc = pkgs.runCommand "custom-etc" {} ''
        mkdir -p $out/etc
        echo 'root:x:0:0:root user:/var/empty:/bin/sh' > $out/etc/passwd
        echo 'nobody:x:65534:65534:nobody:/var/empty:/bin/sh' >> $out/etc/passwd
        echo 'researcher:x:1000:1000:Research Stack developer:/home/researcher:/bin/bash' >> $out/etc/passwd
        echo 'root:x:0:' > $out/etc/group
        echo 'nobody:x:65534:' >> $out/etc/group
        echo 'researcher:x:1000:' >> $out/etc/group
        echo 'passwd: files' > $out/etc/nsswitch.conf
        echo 'group: files' >> $out/etc/nsswitch.conf
        echo 'hosts: files dns' >> $out/etc/nsswitch.conf
      '';

      researcherSetup = pkgs.runCommand "researcher-home" {} ''
        mkdir -p $out/home/researcher/stack
        mkdir -p $out/home/researcher/.elan/toolchains
        mkdir -p $out/home/researcher/.cache
        mkdir -p -m 1777 $out/tmp
        chmod 755 $out/home/researcher
        chmod 700 $out/home/researcher/.elan
      '';

    in rec {
      packages.${system} = {
        inherit corePackages pythonPackages mathPackages;

        # ── Lean LSP service (port 8765) ──────────────────────────────────
        lean-lsp-mcp = elan-lsp { toolchain = "4.19.0"; port = 8765; };

        # ── Lean LSP with mathlib toolchain (port 8766) ───────────────────
        lean-lsp-mathlib = elan-lsp { toolchain = "4.30.0-rc2"; port = 8766; };

        # ── Python LSP TCP (port 8767) ───────────────────────────────────
        pylsp = pylsp-tcp { port = 8767; };

        # ── Ollama inference server ───────────────────────────────────────
        ollama = ollama-service;
      };

      # ── NixOS configuration for the VPS ──────────────────────────────────
      nixosConfigurations.netcup-vps = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ./configuration.nix
        ];
      };

      # Convenience: nix build .#packages.aarch64-linux.lean-lsp-mcp
      defaultPackage.${system} = packages.${system}.lean-lsp-mcp;

      # ── Dev shell ───────────────────────────────────────────────────────
      devShells.${system}.default = pkgs.mkShell {
        packages = corePackages ++ pythonPackages ++ mathPackages;
        shellHook = ''
          echo "Research Stack — netcup VPS dev shell (ARM64, NixOS 25.11)"
          export PS1='\[\033[1;34m\][rs-vps]\[\033[0m\] \w \$ '
        '';
      };
    };
}
