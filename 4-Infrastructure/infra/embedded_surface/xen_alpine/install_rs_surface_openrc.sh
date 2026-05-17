#!/bin/sh
set -eu

SERVICE_USER="${SERVICE_USER:-surface}"
SERVICE_GROUP="${SERVICE_GROUP:-surface}"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/rs-surface}"
CONFIG_DIR="${CONFIG_DIR:-/etc/rs-surface}"
STATE_DIR="${STATE_DIR:-/var/lib/rs-surface}"
LOG_DIR="${LOG_DIR:-/var/log/rs-surface}"
RUN_DIR="${RUN_DIR:-/run/rs-surface}"
MOUNT_DIR="${MOUNT_DIR:-/mnt/topological-storage}"
SOURCE_ROOT="${SOURCE_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PROFILE_SRC="${PROFILE_SRC:-$SOURCE_ROOT/profiles/xen-alpine-surface.json}"
SERVER_SRC="${SERVER_SRC:-$SOURCE_ROOT/server.py}"
SERVICE_SRC="${SERVICE_SRC:-$(cd "$(dirname "$0")" && pwd)/rs-surface.openrc}"

need_root() {
  if [ "$(id -u)" != "0" ]; then
    echo "install_rs_surface_openrc.sh must run as root" >&2
    exit 1
  fi
}

install_packages() {
  if command -v apk >/dev/null 2>&1; then
    apk add --no-cache python3 ca-certificates >/dev/null
  fi
}

ensure_user() {
  if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
    addgroup -S "$SERVICE_GROUP"
  fi
  if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    adduser -S -D -H -G "$SERVICE_GROUP" "$SERVICE_USER"
  fi
}

install_surface() {
  test -f "$SERVER_SRC"
  test -f "$PROFILE_SRC"
  test -f "$SERVICE_SRC"

  mkdir -p "$INSTALL_ROOT" "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR" "$RUN_DIR" "$MOUNT_DIR"
  install -m 0755 "$SERVER_SRC" "$INSTALL_ROOT/server.py"
  install -m 0644 "$PROFILE_SRC" "$CONFIG_DIR/node.json"
  install -m 0755 "$SERVICE_SRC" /etc/init.d/rs-surface
  chown -R "$SERVICE_USER:$SERVICE_GROUP" "$STATE_DIR" "$LOG_DIR" "$RUN_DIR" "$MOUNT_DIR"
}

enable_service() {
  if command -v rc-update >/dev/null 2>&1; then
    rc-update add rs-surface default >/dev/null
  fi
}

need_root
install_packages
ensure_user
install_surface
enable_service

cat <<EOF
installed rs-surface
  server:  $INSTALL_ROOT/server.py
  profile: $CONFIG_DIR/node.json
  service: /etc/init.d/rs-surface

start with:
  rc-service rs-surface start
EOF
