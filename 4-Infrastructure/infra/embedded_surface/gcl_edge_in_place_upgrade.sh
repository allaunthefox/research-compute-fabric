#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-rs-surface-api.service}"
CURRENT_SERVER="${CURRENT_SERVER:-/opt/rs-surface/current/rs-surface}"
CURRENT_PROFILE="${CURRENT_PROFILE:-/etc/rs-surface/node.json}"
STATE_DIR="${STATE_DIR:-/var/lib/rs-surface}"
MOUNT_DIR="${MOUNT_DIR:-/mnt/topological-storage}"
ROLLBACK_ROOT="${ROLLBACK_ROOT:-$STATE_DIR/rollback}"
TEMP_HOST="${TEMP_HOST:-127.0.0.1}"
TEMP_PORT="${TEMP_PORT:-18080}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/health}"

usage() {
  cat <<'USAGE'
Usage:
  gcl_edge_in_place_upgrade.sh upgrade <rs-surface-binary> <node.json>
  gcl_edge_in_place_upgrade.sh rollback <rollback-dir>

Environment overrides:
  SERVICE_NAME      systemd service to restart, default rs-surface-api.service
  CURRENT_SERVER    installed server path, default /opt/rs-surface/current/rs-surface
  CURRENT_PROFILE   installed profile path, default /etc/rs-surface/node.json
  STATE_DIR         surface state dir, default /var/lib/rs-surface
  MOUNT_DIR         topology mount dir, default /mnt/topological-storage
  HEALTH_URL        post-restart health URL, default http://127.0.0.1:8080/health
  TEMP_PORT         smoke-test port, default 18080
USAGE
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "must run as root" >&2
    exit 1
  fi
}

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

health_check() {
  local url="$1"
  python3 - "$url" <<'PY'
import json
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=5) as response:
    payload = json.loads(response.read().decode("utf-8"))
if payload.get("ok") is not True:
    raise SystemExit(f"health not ok: {payload!r}")
print(json.dumps(payload, sort_keys=True))
PY
}

validate_inputs() {
  local server_src="$1"
  local profile_src="$2"

  test -f "$server_src"
  test -x "$server_src"
  test -f "$profile_src"
  python3 -m json.tool "$profile_src" >/dev/null
}

smoke_test_candidate() {
  local server_src="$1"
  local profile_src="$2"
  local smoke_state
  smoke_state="$(mktemp -d)"
  local pid=""

  cleanup_smoke() {
    trap - RETURN
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
    rm -rf "$smoke_state"
  }
  trap cleanup_smoke RETURN

  RS_SURFACE_PROFILE="$profile_src" \
    RS_SURFACE_STATE="$smoke_state" \
    RS_SURFACE_MOUNT="$MOUNT_DIR" \
    RS_SURFACE_HOST="$TEMP_HOST" \
    RS_SURFACE_PORT="$TEMP_PORT" \
    "$server_src" >/tmp/rs-surface-upgrade-smoke.log 2>&1 &
  pid="$!"

  for _ in 1 2 3 4 5; do
    if health_check "http://$TEMP_HOST:$TEMP_PORT/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "candidate smoke test failed; log follows:" >&2
  sed -n '1,120p' /tmp/rs-surface-upgrade-smoke.log >&2 || true
  return 1
}

save_current() {
  local rollback_dir="$1"
  mkdir -p "$rollback_dir"
  if [ -f "$CURRENT_SERVER" ]; then
    install -m 0755 "$CURRENT_SERVER" "$rollback_dir/rs-surface"
  fi
  if [ -f "$CURRENT_PROFILE" ]; then
    install -m 0644 "$CURRENT_PROFILE" "$rollback_dir/node.json"
  fi
  systemctl cat "$SERVICE_NAME" >"$rollback_dir/$SERVICE_NAME.cat" 2>/dev/null || true
}

write_last_good() {
  local server_path="$1"
  local profile_path="$2"
  mkdir -p "$STATE_DIR"
  cat >"$STATE_DIR/last-good.json" <<EOF
{"ok":true,"updated_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","mode":"in-place","service":"$SERVICE_NAME","server_sha256":"$(sha256_of "$server_path")","profile_sha256":"$(sha256_of "$profile_path")"}
EOF
}

restore_from() {
  local rollback_dir="$1"
  test -d "$rollback_dir"
  test -f "$rollback_dir/rs-surface"
  test -f "$rollback_dir/node.json"

  install -d -m 0755 "$(dirname "$CURRENT_SERVER")"
  install -d -m 0755 "$(dirname "$CURRENT_PROFILE")"
  install -m 0755 "$rollback_dir/rs-surface" "$CURRENT_SERVER"
  install -m 0644 "$rollback_dir/node.json" "$CURRENT_PROFILE"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME"
  health_check "$HEALTH_URL" >/dev/null
  write_last_good "$CURRENT_SERVER" "$CURRENT_PROFILE"
  echo "rolled back using $rollback_dir"
}

upgrade() {
  local server_src="$1"
  local profile_src="$2"
  local ts rollback_dir
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  rollback_dir="$ROLLBACK_ROOT/inplace-$ts"

  validate_inputs "$server_src" "$profile_src"
  smoke_test_candidate "$server_src" "$profile_src"
  save_current "$rollback_dir"

  install -d -m 0755 "$(dirname "$CURRENT_SERVER")"
  install -d -m 0755 "$(dirname "$CURRENT_PROFILE")"
  install -d -m 0755 "$STATE_DIR"
  install -m 0755 "$server_src" "$CURRENT_SERVER"
  install -m 0644 "$profile_src" "$CURRENT_PROFILE"

  systemctl daemon-reload
  if ! systemctl restart "$SERVICE_NAME"; then
    echo "restart failed; restoring $rollback_dir" >&2
    restore_from "$rollback_dir"
    exit 1
  fi

  if ! health_check "$HEALTH_URL" >/dev/null; then
    echo "post-upgrade health failed; restoring $rollback_dir" >&2
    restore_from "$rollback_dir"
    exit 1
  fi

  write_last_good "$CURRENT_SERVER" "$CURRENT_PROFILE"
  echo "in-place upgrade complete"
  echo "rollback: $rollback_dir"
}

case "${1:-}" in
  upgrade)
    if [ "$#" -ne 3 ]; then
      usage >&2
      exit 2
    fi
    require_root
    upgrade "$2" "$3"
    ;;
  rollback)
    if [ "$#" -ne 2 ]; then
      usage >&2
      exit 2
    fi
    require_root
    restore_from "$2"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
