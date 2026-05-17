FROM alpine:3.19

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
    && :

RUN pipx install uv && cp /root/.local/bin/uv /usr/local/bin/uv && cp /root/.local/bin/uvx /usr/local/bin/uvx

RUN adduser -D -u 1000 researcher

ENV PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/home/researcher/.cache

COPY --chown=researcher:researcher . /home/researcher/stack

USER researcher
RUN uv python install 3.11.15 \
    && uv venv --clear --python 3.11.15 /home/researcher/venv \
    && uv pip install --python /home/researcher/venv/bin/python3 \
        biopython \
        networkx \
        pycryptodome \
        zstandard \
        z3-solver \
        PyWavelets \
    && :

ENV PATH="/home/researcher/venv/bin:/home/researcher/.local/bin:${PATH}"
WORKDIR /home/researcher/stack

CMD ["/bin/bash"]
