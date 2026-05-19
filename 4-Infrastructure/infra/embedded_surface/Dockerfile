# ── Stage 1: build the Rust surface binary ─────────────────────────────────
FROM rust:1.82-alpine AS builder

RUN apk add --no-cache musl-dev openssl-dev openssl-libs-static pkgconfig

WORKDIR /build
COPY rs-surface/Cargo.toml rs-surface/Cargo.lock ./
# Pre-fetch deps (layer cache)
RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release 2>/dev/null || true

COPY rs-surface/src ./src
RUN touch src/main.rs && cargo build --release

# ── Stage 2: minimal runtime image ─────────────────────────────────────────
FROM alpine:3.20

ENV RS_SURFACE_PROFILE=/etc/rs-surface/node.json
ENV RS_SURFACE_STATE=/var/lib/rs-surface
ENV RS_SURFACE_MOUNT=/mnt/topological-storage
ENV RS_SURFACE_HOST=0.0.0.0
ENV RS_SURFACE_PORT=8080

RUN adduser -D -H -u 988 surface \
    && mkdir -p /opt/rs-surface /etc/rs-surface /var/lib/rs-surface /var/log/rs-surface /run/rs-surface /mnt/topological-storage \
    && chown -R surface:surface /var/lib/rs-surface /var/log/rs-surface /run/rs-surface /mnt/topological-storage

COPY --from=builder /build/target/release/rs-surface /opt/rs-surface/rs-surface
COPY profiles/racknerd-surface.json /etc/rs-surface/node.json

# Keep the Python server alongside for fallback / debugging
COPY server.py /opt/rs-surface/server.py

USER surface
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:${RS_SURFACE_PORT}/health || exit 1

CMD ["/opt/rs-surface/rs-surface"]
