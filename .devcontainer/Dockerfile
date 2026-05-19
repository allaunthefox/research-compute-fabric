FROM nixos/nix:latest

# ── Nix configuration: enable flakes + nix-command ───────────────────────────
RUN mkdir -p /etc/nix && \
    echo 'experimental-features = nix-command flakes' >> /etc/nix/nix.conf && \
    echo 'sandbox = false' >> /etc/nix/nix.conf

# ── System packages via nix profile ──────────────────────────────────────────
# This mirrors the devPkgs set in flake.nix (authoritative build path).
# The canonical image is produced by `nix build .#devcontainer` on the host;
# this Dockerfile is a self-contained fallback that produces an equivalent env.
RUN nix profile install \
    nixpkgs#bash \
    nixpkgs#bashInteractive \
    nixpkgs#coreutils \
    nixpkgs#findutils \
    nixpkgs#gnugrep \
    nixpkgs#gnused \
    nixpkgs#gawk \
    nixpkgs#util-linux \
    nixpkgs#git \
    nixpkgs#git-lfs \
    nixpkgs#curl \
    nixpkgs#wget \
    nixpkgs#rsync \
    nixpkgs#zstd \
    nixpkgs#xz \
    nixpkgs#gnutar \
    nixpkgs#gzip \
    nixpkgs#ripgrep \
    nixpkgs#jq \
    nixpkgs#gnumake \
    nixpkgs#nodejs_20 \
    nixpkgs#uv \
    nixpkgs#elan \
    nixpkgs#postgresql_16 \
    nixpkgs#graphviz \
    nixpkgs#openssh \
    nixpkgs#cacert \
    nixpkgs#less \
    nixpkgs#which \
    nixpkgs#file \
    nixpkgs#procps \
    nixpkgs#htop \
    nixpkgs#rclone \
    nixpkgs#iproute2 \
    nixpkgs#pkg-config \
    nixpkgs#openssl \
    nixpkgs#gcc \
    nixpkgs#binutils \
    nixpkgs#glibc \
    nixpkgs#libglvnd \
    nixpkgs#xorg.libX11 \
    nixpkgs#xorg.libXext \
    nixpkgs#xorg.libXrender \
    nixpkgs#mesa \
    && nix-collect-garbage -d

# ── LaTeX + typesetting ───────────────────────────────────────────────────────
RUN nix profile install \
    nixpkgs#texliveFull \
    nixpkgs#typst \
    && nix-collect-garbage -d

# ── Math / science CLI ────────────────────────────────────────────────────────
RUN nix profile install \
    nixpkgs#gnuplot \
    nixpkgs#maxima \
    nixpkgs#wxmaxima \
    nixpkgs#octave \
    nixpkgs#sage \
    && nix-collect-garbage -d

# ── Typst (already installed above via nix) ───────────────────────────────────
# typst is available from nixpkgs#typst — no separate binary download needed.

# ── Tailscale (static binary — userspace networking, no root required) ────────
RUN TSVER=$(curl -fsSL https://pkgs.tailscale.com/stable/ \
      | grep -oP 'tailscale_\K[0-9]+\.[0-9]+\.[0-9]+(?=_amd64\.tgz)' \
      | sort -V | tail -1) \
    && curl -fsSL "https://pkgs.tailscale.com/stable/tailscale_${TSVER}_amd64.tgz" \
       | tar -xz -C /tmp/ \
    && install -m 755 /tmp/tailscale_${TSVER}_amd64/tailscale  /usr/local/bin/tailscale \
    && install -m 755 /tmp/tailscale_${TSVER}_amd64/tailscaled /usr/local/bin/tailscaled \
    && rm -rf /tmp/tailscale_${TSVER}_amd64

# ── Non-root developer user 'researcher' (UID 1000) ──────────────────────────
RUN useradd -m -u 1000 -s /bin/bash researcher

ENV PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/home/researcher/.cache \
    UV_LINK_MODE=copy \
    SSL_CERT_FILE=/root/.nix-profile/etc/ssl/certs/ca-bundle.crt \
    NIX_SSL_CERT_FILE=/root/.nix-profile/etc/ssl/certs/ca-bundle.crt

USER researcher
WORKDIR /home/researcher/stack

# ── Python 3.11 venv + all repo-required packages ────────────────────────────
RUN uv python install 3.11.15 \
    && uv venv --clear --python 3.11.15 /home/researcher/venv

RUN uv pip install --python /home/researcher/venv/bin/python3 \
    # AWS + RDS IAM auth
    boto3 \
    botocore \
    # Postgres
    psycopg2-binary \
    # HTTP clients
    requests \
    httpx \
    # API server (swarm API, credential server)
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    # Notion + Linear clients
    notion-client \
    # Data / serialisation
    python-dotenv \
    pyyaml \
    rich \
    # Science / math baseline
    biopython \
    networkx \
    pycryptodome \
    zstandard \
    z3-solver \
    PyWavelets \
    # Numerics
    numpy \
    scipy \
    # Arbitrary-precision arithmetic
    mpmath \
    # Plotting / visualisation
    matplotlib \
    seaborn \
    # Data frames
    pandas \
    polars \
    # Machine learning
    scikit-learn \
    # Search / web
    beautifulsoup4 \
    lxml \
    # Lean / symbolic
    sympy \
    # Testing
    pytest \
    && :

# ── elan (Lean 4 Version Manager) ────────────────────────────────────────────
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf \
    | sh -s -- -y --default-toolchain leanprover/lean4:stable

# ── PATH ──────────────────────────────────────────────────────────────────────
ENV PATH="/home/researcher/.elan/bin:/home/researcher/venv/bin:/home/researcher/.local/bin:${PATH}"

# ── Tailscale userspace auto-start snippet ────────────────────────────────────
RUN mkdir -p /home/researcher/.local/share/tailscale && \
    printf '%s\n' \
      '# ── Tailscale (userspace, no root required) ─────────────────────────────' \
      'export TAILSCALE_SOCKET=/home/researcher/.local/share/tailscale/tailscaled.sock' \
      'alias tailscale="tailscale --socket=$TAILSCALE_SOCKET"' \
      '_ts_start() {' \
      '  if ! /usr/local/bin/tailscale --socket=$TAILSCALE_SOCKET status &>/dev/null; then' \
      '    mkdir -p /home/researcher/.local/share/tailscale' \
      '    /usr/local/bin/tailscaled \\' \
      '      --tun=userspace-networking \\' \
      '      --socket=$TAILSCALE_SOCKET \\' \
      '      --statedir=/home/researcher/.local/share/tailscale/ \\' \
      '      --outbound-http-proxy-listen=localhost:1055 \\' \
      '      &>>/home/researcher/.local/share/tailscale/tailscaled.log &' \
      '    sleep 2' \
      '  fi' \
      '}' \
      '_ts_start' \
      >> /home/researcher/.bashrc

# ── rclone S3 gateway init script ─────────────────────────────────────────────
COPY --chown=researcher:researcher .devcontainer/init-rclone-s3.sh /home/researcher/init-rclone-s3.sh
RUN chmod +x /home/researcher/init-rclone-s3.sh

ENTRYPOINT ["/home/researcher/init-rclone-s3.sh"]
CMD ["/bin/bash"]
