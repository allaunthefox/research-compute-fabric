FROM alpine:3.19

# ── System packages ───────────────────────────────────────────────────────────
# Core build + dev tools
RUN apk add --no-cache \
    bash \
    build-base \
    git \
    curl \
    wget \
    openssh-client \
    rsync \
    zstd \
    jq \
    ripgrep \
    # Graphviz for visualisation helpers
    graphviz \
    # Node / npm for JS tooling
    nodejs \
    npm \
    # Python runtime + package managers
    python3 \
    py3-pip \
    pipx \
    # PostgreSQL client libs (needed by psycopg2 --no-binary build)
    postgresql16-client \
    postgresql16-dev \
    libpq-dev \
    # SSL / crypto headers (boto3, requests, psycopg2)
    openssl-dev \
    # CFFI / ffi headers
    libffi-dev \
    # Needed for some science packages (scipy, etc.)
    gfortran \
    openblas-dev \
    lapack-dev \
    # Misc compression
    xz \
    bzip2-dev \
    # rclone (Google Drive / S3 / etc.)
    rclone \
    && :

# ── uv package manager ────────────────────────────────────────────────────────
RUN pipx install uv && cp /root/.local/bin/uv /usr/local/bin/uv && cp /root/.local/bin/uvx /usr/local/bin/uvx

# ── Non-root developer user 'researcher' (UID 1000) ──────────────────────────
RUN adduser -D -u 1000 researcher

ENV PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/home/researcher/.cache \
    UV_LINK_MODE=copy

USER researcher
WORKDIR /home/researcher/stack

# ── Python 3.11 venv + all repo-required packages ────────────────────────────
RUN uv python install 3.11.15 \
    && uv venv --clear --python 3.11.15 /home/researcher/venv

# Core infrastructure / ingestion dependencies
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
    # Science / math baseline (from requirements-optional-science.txt)
    biopython \
    networkx \
    pycryptodome \
    zstandard \
    z3-solver \
    PyWavelets \
    # galois>=0.4 needs numba->llvmlite which requires LLVM; install separately on host if needed
    # Numerics
    numpy \
    scipy \
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

# ── rclone S3 gateway init script ─────────────────────────────────────────────
COPY --chown=researcher:researcher .devcontainer/init-rclone-s3.sh /home/researcher/init-rclone-s3.sh
RUN chmod +x /home/researcher/init-rclone-s3.sh

ENTRYPOINT ["/home/researcher/init-rclone-s3.sh"]
CMD ["/bin/bash"]
