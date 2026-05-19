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

      # ── Dev shell packages ──────────────────────────────────────────────────
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
        # File transfer & compression
        curl
        wget
        rsync
        zstd
        xz
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
      ];

      # ── fakeNss provides /etc/passwd, /etc/group with root + nobody ─────────
      # We add researcher (UID 1000) via a setup derivation.
      researcherSetup = pkgs.runCommand "researcher-home" {} ''
        mkdir -p $out/home/researcher/stack
        mkdir -p $out/home/researcher/.cache
        mkdir -p $out/tmp
        # passwd / group entries appended by the image config
      '';

    in {
      # ── Layered OCI image for the devcontainer ──────────────────────────────
      packages.${system}.devcontainer = pkgs.dockerTools.buildLayeredImage {
        name   = "research-stack-otom";
        tag    = "latest";

        contents = [
          pkgs.dockerTools.fakeNss   # /etc/passwd, /etc/group, /etc/nsswitch.conf
          pkgs.dockerTools.usrBinEnv # /usr/bin/env
          pkgs.dockerTools.binSh     # /bin/sh -> bash
          researcherSetup
        ] ++ devPkgs;

        # Write researcher user entries into /etc/passwd and /etc/group.
        # fakeNss creates these files; we append with a sed-safe runCommand.
        fakeRootCommands = ''
          # Add researcher user (UID/GID 1000)
          echo 'researcher:x:1000:1000:Research Stack developer:/home/researcher:/bin/bash' >> ./etc/passwd
          echo 'researcher:x:1000:' >> ./etc/group
          # Ensure home is owned by researcher
          chown -R 1000:1000 ./home/researcher || true
        '';
        enableFakechroot = true;

        config = {
          User       = "1000";
          WorkingDir = "/home/researcher/stack";
          Env = [
            "PATH=/home/researcher/.elan/bin:${pythonEnv}/bin:${pkgs.uv}/bin:${pkgs.git}/bin:${pkgs.ripgrep}/bin:${pkgs.jq}/bin:${pkgs.coreutils}/bin:${pkgs.bashInteractive}/bin:/usr/bin:/bin"
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

      # Convenience alias: `nix build .#devcontainer`
      defaultPackage.${system} = self.packages.${system}.devcontainer;

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
