# Dockerfile — fallback / quick-iteration path for rs-surface.
#
# The CANONICAL build is the Nix flake target:
#   nix build .#rs-surface-image   # produces a deterministic OCI tarball
#   docker load < result
#
# This Dockerfile exists for environments where `nix build` is unavailable
# (e.g. raw Docker CI, RackNerd VPS before Nix is set up).  It uses
# debian:bookworm-slim for glibc compatibility with the standard Rust toolchain.
#
# ── Stage 1: build the Rust surface binary ─────────────────────────────────
FROM rust:1.82-bookworm AS builder

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY rs-surface/Cargo.toml rs-surface/Cargo.lock ./
RUN mkdir src && echo 'fn main(){}' > src/main.rs \
    && cargo build --release 2>/dev/null; rm -f target/release/rs-surface

COPY rs-surface/src ./src
RUN touch src/main.rs && cargo build --release

# ── Stage 2: minimal glibc runtime ─────────────────────────────────────────
FROM debian:bookworm-slim

ENV RS_SURFACE_PROFILE=/etc/rs-surface/node.json
ENV RS_SURFACE_STATE=/var/lib/rs-surface
ENV RS_SURFACE_MOUNT=/mnt/topological-storage
ENV RS_SURFACE_HOST=0.0.0.0
ENV RS_SURFACE_PORT=8080

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    ca-certificates wget && rm -rf /var/lib/apt/lists/* \
    && adduser --system --no-create-home --uid 988 surface \
    && mkdir -p /opt/rs-surface /etc/rs-surface /var/lib/rs-surface \
                /var/log/rs-surface /run/rs-surface /mnt/topological-storage \
    && chown -R surface:surface /var/lib/rs-surface /var/log/rs-surface \
                                /run/rs-surface /mnt/topological-storage

COPY --from=builder /build/target/release/rs-surface /opt/rs-surface/rs-surface
COPY profiles/racknerd-surface.json /etc/rs-surface/node.json

# Python server kept alongside as a debugging/fallback reference
COPY server.py /opt/rs-surface/server.py

USER surface
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:${RS_SURFACE_PORT}/health || exit 1

CMD ["/opt/rs-surface/rs-surface"]
