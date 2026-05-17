FROM alpine:3.19

# Install system development libraries + git + curl + ssh clients
RUN apk add --no-cache \
    bash \
    build-base \
    nodejs \
    npm \
    pipx \
    py3-pip \
    python3 \
    rsync \
    zstd \
    graphviz \
    git \
    curl \
    openssh-client \
    && :

# Install uv package manager
RUN pipx install uv && cp /root/.local/bin/uv /usr/local/bin/uv && cp /root/.local/bin/uvx /usr/local/bin/uvx

# Add non-root developer user 'researcher' matching default host UID
RUN adduser -D -u 1000 researcher

ENV PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/home/researcher/.cache

USER researcher
WORKDIR /home/researcher/stack

# Install python toolchains and standard math-discovery libraries inside virtualenv
RUN uv python install 3.11.15 \
    && uv venv --clear --python 3.11.15 /home/researcher/venv \
    && uv pip install --python /home/researcher/venv/bin/python3 \
        biopython \
        networkx \
        pycryptodome \
        zstandard \
        z3-solver \
        PyWavelets

# Install elan (Lean 4 Version Manager) for mathematically proven integer arithmetic compilation
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y --default-toolchain leanprover/lean4:stable

# Add toolchains to path
ENV PATH="/home/researcher/.elan/bin:/home/researcher/venv/bin:/home/researcher/.local/bin:${PATH}"

CMD ["/bin/bash"]
