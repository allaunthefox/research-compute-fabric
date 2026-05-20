{
  description = "Research Stack — dev-container image + NixOS topology";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs   = import nixpkgs { inherit system; config.allowUnfree = false; };

      # ── Python environment ──────────────────────────────────────────────────
      # All packages the repo scripts actually import, derived from:
      #   4-Infrastructure/infra/requirements_knowledge.txt
      #   5-Applications/requirements_swarm_api.txt
      #   requirements-optional-science.txt
      #   4-Infrastructure/shim/notion_linear_rds_ingest.py imports
      pythonEnv = pkgs.python311.withPackages (ps: with ps; [
        # AWS / RDS
        boto3
        botocore
        # PostgreSQL
        psycopg2
        # HTTP
        requests
        httpx
        # API framework
        fastapi
        uvicorn
        pydantic
        # YAML / env / serialisation
        python-dotenv
        pyyaml
        rich
        # Science / math
        biopython
        networkx
        pycryptodome
        zstandard
        z3
        pywavelets
        numpy
        scipy
        sympy
        # Arbitrary-precision arithmetic
        mpmath
        # Plotting / visualisation
        matplotlib
        seaborn
        # Data frames
        pandas
        polars
        # Machine learning
        scikit-learn
        # Web scraping
        beautifulsoup4
        lxml
        # Notion SDK
        notion-client
        # Testing
        pytest
        # Misc stdlib extras
        python-dateutil
        urllib3
      ]);

      # ── R environment with tidyverse + ggplot2 ─────────────────────────────
      rEnv = pkgs.rWrapper.override {
        packages = with pkgs.rPackages; [
          tidyverse
          ggplot2
          dplyr
          tidyr
          readr
          purrr
          stringr
          forcats
          lubridate
          # Statistical extras
          MASS
          Matrix
          survival
          # Output
          knitr
          rmarkdown
        ];
      };

      devPkgs = with pkgs; [
        # Version control
        git
        git-lfs
        # Shells & core utils
        bash
        bashInteractive
        coreutils
        findutils
        gnugrep
        gnused
        gawk
        util-linux # for flock
        # File transfer & compression
        curl
        wget
        rsync
        zstd
        xz
        gnutar
        gzip
        # Search
        ripgrep
        jq
        # Build essentials (light — no full gcc toolchain in image)
        gnumake
        # Node / npm for JS tooling
        nodejs_20
        # Python: uv for runtime package installs + the full pre-built env
        uv
        pythonEnv
        # Lean 4 via elan
        elan
        # PostgreSQL client (psql, pg_dump)
        postgresql_16
        # Graphviz
        graphviz
        # Network / TLS
        openssh
        cacert
        # Shell helpers
        less
        which
        file
        procps
        htop
        # glibc for ldd
        glibc
        # binutils for ldd
        binutils
        # gcc for libstdc++.so.6 (needed by VS Code server)
        gcc
        # OpenGL / X11 libraries for CAD (build123d, OCP, VTK) and GPU compute
        libglvnd
        xorg.libX11
        xorg.libXext
        xorg.libXrender
        mesa
        # pkg-config for Rust native dependency discovery (openssl-sys, etc.)
        pkg-config
        openssl
        # ── LaTeX ──────────────────────────────────────────────────────────────
        # texliveFull: complete TeX Live distribution (~5 GB) — every package
        # pre-cached in the image so latex/xelatex/lualatex/latexmk all work
        # offline. Use texliveMedium to trade completeness for image size.
        texliveFull
        # ── Math / science CLI ─────────────────────────────────────────────────
        gnuplot          # publication-quality 2-D/3-D scientific plotting
        maxima           # full CAS: symbolic algebra, calculus, ODEs
        wxmaxima         # GUI front-end for maxima
        octave           # GNU Octave — MATLAB-compatible numerics
        rEnv             # R + tidyverse / ggplot2 (see rEnv binding above)
        # ── Typesetting ────────────────────────────────────────────────────────
        typst            # modern markup-based typesetting (LaTeX alternative)
        # ── CAS ────────────────────────────────────────────────────────────────
        sage             # SageMath 10.5 — full open-source mathematics system
      ];

      # ── customEtc provides standard etc configuration with researcher user ──
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

      # We add researcher home/tmp via a setup derivation.
      researcherSetup = pkgs.runCommand "researcher-home" {} ''
        mkdir -p $out/home/researcher/stack
        mkdir -p $out/home/researcher/.cache
        mkdir -p -m 1777 $out/tmp
      '';

      # ── rs-surface binary ───────────────────────────────────────────────────
      # Rust port of 4-Infrastructure/infra/embedded_surface/server.py.
      # Build the binary hermetically via rustPlatform.buildRustPackage.
      #
      # cargoHash: run `nix build .#rs-surface 2>&1 | grep "got:"` to get the
      # real hash after any Cargo.lock change, then replace lib.fakeHash below.
      rsSurface = pkgs.rustPlatform.buildRustPackage {
        pname   = "rs-surface";
        version = "0.1.0";

        src = pkgs.lib.cleanSource ./4-Infrastructure/infra/embedded_surface/rs-surface;

        cargoLock.lockFile = ./4-Infrastructure/infra/embedded_surface/rs-surface/Cargo.lock;

        nativeBuildInputs = [ pkgs.pkg-config ];
        buildInputs       = [ pkgs.openssl ];

        meta = {
          description = "Embedded node surface daemon (Rust)";
          license     = pkgs.lib.licenses.mit;
          mainProgram = "rs-surface";
        };
      };

      # ── Minimal OCI image for the embedded node surface ────────────────────
      # Built entirely from the Nix store — no Dockerfile, no Alpine, no musl.
      # The closure contains only the binary + its glibc runtime deps.
      #
      # Build:  nix build .#rs-surface-image
      # Load:   docker load < result
      # Run:    docker run --rm -p 8080:8080 -v /etc/rs-surface:/etc/rs-surface rs-surface:latest
      rsSurfaceImage = pkgs.dockerTools.buildLayeredImage {
        name = "rs-surface";
        tag  = "latest";

        contents = [
          rsSurface
          pkgs.cacert          # TLS roots (for any outbound HTTPS)
          pkgs.coreutils       # minimal shell utilities for healthcheck
        ];

        # /etc/rs-surface/node.json is volume-mounted at runtime; create the
        # directory so the mount point exists in the image.
        extraCommands = ''
          mkdir -p etc/rs-surface var/lib/rs-surface mnt/topological-storage
        '';

        config = {
          Entrypoint = [ "${rsSurface}/bin/rs-surface" ];
          Env = [
            "RS_SURFACE_PROFILE=/etc/rs-surface/node.json"
            "RS_SURFACE_STATE=/var/lib/rs-surface"
            "RS_SURFACE_MOUNT=/mnt/topological-storage"
            "RS_SURFACE_HOST=0.0.0.0"
            "RS_SURFACE_PORT=8080"
            "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
          ];
          ExposedPorts = { "8080/tcp" = {}; };
          Healthcheck = {
            Test        = [ "CMD" "${pkgs.coreutils}/bin/sh" "-c"
              "wget -qO- http://127.0.0.1:8080/health || exit 1" ];
            Interval    = 10000000000;   # 10 s in nanoseconds
            Timeout     = 3000000000;    # 3 s
            StartPeriod = 3000000000;    # 3 s
            Retries     = 3;
          };
          Labels = {
            "org.opencontainers.image.description" = "rs-surface embedded node daemon";
            "org.opencontainers.image.source"      = "4-Infrastructure/infra/embedded_surface/rs-surface";
          };
        };

        maxLayers = 10;
      };

    in rec {
      packages.${system} = {

        # ── Layered OCI image for the devcontainer ────────────────────────────
        devcontainer = pkgs.dockerTools.buildLayeredImage {
          name   = "research-stack-otom";
          tag    = "latest";

          contents = [
            customEtc                  # Custom etc configuration containing researcher user
            pkgs.dockerTools.usrBinEnv # /usr/bin/env
            pkgs.dockerTools.binSh     # /bin/sh -> bash
            researcherSetup
          ] ++ devPkgs;

          # Ensure home is owned by researcher
          fakeRootCommands = ''
            chown -R 1000:1000 ./home/researcher || true
            chmod 1777 ./tmp || true
          '';
          enableFakechroot = true;

          config = {
            User       = "1000";
            WorkingDir = "/home/researcher/stack";
            Env = [
              "PATH=/home/researcher/.elan/bin:${pythonEnv}/bin:${pkgs.uv}/bin:${pkgs.git}/bin:${pkgs.ripgrep}/bin:${pkgs.jq}/bin:${pkgs.coreutils}/bin:${pkgs.bashInteractive}/bin:${pkgs.binutils}/bin:${pkgs.glibc.bin}/bin:${pkgs.gzip}/bin:${pkgs.pkg-config}/bin:${pkgs.openssl.bin}/bin:${pkgs.texliveFull}/bin:${pkgs.typst}/bin:${pkgs.gnuplot}/bin:${pkgs.maxima}/bin:${pkgs.octave}/bin:${rEnv}/bin:${pkgs.sage}/bin:/usr/bin:/bin"
              "LD_LIBRARY_PATH=${pkgs.gcc.cc.lib}/lib:${pkgs.glibc}/lib:${pkgs.libglvnd}/lib:${pkgs.xorg.libX11}/lib:${pkgs.xorg.libXext}/lib:${pkgs.xorg.libXrender}/lib:${pkgs.mesa}/lib:${pkgs.openssl}/lib"
              "PYTHONUNBUFFERED=1"
              "XDG_CACHE_HOME=/home/researcher/.cache"
              "HOME=/home/researcher"
              "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
              "NIX_SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
            ];
            Cmd = [ "${pkgs.bashInteractive}/bin/bash" ];
          };

          maxLayers = 120;
        };

        # rs-surface binary and OCI image
        rs-surface       = rsSurface;
        rs-surface-image = rsSurfaceImage;
      };

      # Convenience alias: `nix build .#devcontainer`
      defaultPackage.${system} = packages.${system}.devcontainer;

      # ── Dev shell — `nix develop` on the host (if nix is installed) ─────────
      devShells.${system}.default = pkgs.mkShell {
        packages = devPkgs;
        shellHook = ''
          echo "Research Stack dev shell — NixOS 24.11"
          export PS1='\[\033[1;34m\][rs-dev]\[\033[0m\] \w \$ '
        '';
      };
    };
}
