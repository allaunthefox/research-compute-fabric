#!/bin/sh
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
SURFACE_ROOT="$(cd "$HERE/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$HERE/build/qemu-alpine}"
ASSET_DIR="$BUILD_DIR/assets"
APKOVL_DIR="$BUILD_DIR/apkovl"
LOG_DIR="$BUILD_DIR/logs"
RECEIPT="${RECEIPT:-$BUILD_DIR/qemu-smoke-receipt.json}"
SERIAL_LOG="${SERIAL_LOG:-$LOG_DIR/serial.log}"
PID_FILE="$BUILD_DIR/qemu.pid"

ALPINE_BASE_URL="${ALPINE_BASE_URL:-https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86_64/netboot}"
ALPINE_REPO_URL="${ALPINE_REPO_URL:-https://dl-cdn.alpinelinux.org/alpine/latest-stable/main}"
HOST_PORT="${HOST_PORT:-18081}"
GUEST_PORT="${GUEST_PORT:-8080}"
MEMORY_MB="${MEMORY_MB:-256}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"
SURFACE_IMPL="${SURFACE_IMPL:-python}"
STATIC_BIN="${STATIC_BIN:-$HERE/build/rs-surface-static}"
NOLIBC_BIN="${NOLIBC_BIN:-$HERE/build/rs-surface-nolibc}"
if [ "$SURFACE_IMPL" = "static" ] || [ "$SURFACE_IMPL" = "nolibc" ]; then
  BOOT_PKGS="${BOOT_PKGS:-ca-certificates}"
else
  BOOT_PKGS="${BOOT_PKGS:-python3,ca-certificates}"
fi

mkdir -p "$ASSET_DIR" "$APKOVL_DIR" "$LOG_DIR"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

fetch_asset() {
  name="$1"
  if [ ! -s "$ASSET_DIR/$name" ]; then
    echo "fetching Alpine netboot asset: $name" >&2
    curl -fL "$ALPINE_BASE_URL/$name" -o "$ASSET_DIR/$name"
  fi
}

build_apkovl() {
  rm -rf "$APKOVL_DIR/root"
  mkdir -p \
    "$APKOVL_DIR/root/etc/apk" \
    "$APKOVL_DIR/root/etc/init.d" \
    "$APKOVL_DIR/root/etc/network" \
    "$APKOVL_DIR/root/etc/runlevels/default" \
    "$APKOVL_DIR/root/etc/rs-surface" \
    "$APKOVL_DIR/root/opt/rs-surface"

  printf '%s\n' "$ALPINE_REPO_URL" > "$APKOVL_DIR/root/etc/apk/repositories"
  cat > "$APKOVL_DIR/root/etc/network/interfaces" <<'EOF'
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF
  if [ "$SURFACE_IMPL" = "static" ]; then
    test -x "$STATIC_BIN"
    cp "$STATIC_BIN" "$APKOVL_DIR/root/opt/rs-surface/rs-surface-static"
  elif [ "$SURFACE_IMPL" = "nolibc" ]; then
    test -x "$NOLIBC_BIN"
    cp "$NOLIBC_BIN" "$APKOVL_DIR/root/opt/rs-surface/rs-surface-nolibc"
  else
    cp "$SURFACE_ROOT/server.py" "$APKOVL_DIR/root/opt/rs-surface/server.py"
  fi
  cp "$SURFACE_ROOT/profiles/xen-alpine-surface.json" "$APKOVL_DIR/root/etc/rs-surface/node.json"

  if [ "$SURFACE_IMPL" = "static" ]; then
    cat > "$APKOVL_DIR/root/opt/rs-surface/boot-rs-surface.sh" <<'EOF'
#!/bin/sh
set -eu
echo "rs-surface static qemu bootstrap starting" >&2
mkdir -p /var/lib/rs-surface /var/log/rs-surface /run/rs-surface /mnt/topological-storage
export RS_SURFACE_NODE="${RS_SURFACE_NODE:-xen-alpine-surface}"
export RS_SURFACE_ROLE="${RS_SURFACE_ROLE:-gcl-edge}"
export RS_SURFACE_MODE="${RS_SURFACE_MODE:-recovery}"
export RS_SURFACE_HOST="${RS_SURFACE_HOST:-0.0.0.0}"
export RS_SURFACE_PORT="${RS_SURFACE_PORT:-8080}"
exec /opt/rs-surface/rs-surface-static
EOF
  elif [ "$SURFACE_IMPL" = "nolibc" ]; then
    cat > "$APKOVL_DIR/root/opt/rs-surface/boot-rs-surface.sh" <<'EOF'
#!/bin/sh
set -eu
echo "rs-surface nolibc qemu bootstrap starting" >&2
exec /opt/rs-surface/rs-surface-nolibc
EOF
  else
    cat > "$APKOVL_DIR/root/opt/rs-surface/boot-rs-surface.sh" <<'EOF'
#!/bin/sh
set -eu
echo "rs-surface qemu bootstrap starting" >&2
if ! command -v python3 >/dev/null 2>&1; then
  apk add --no-cache python3 ca-certificates >&2
fi
mkdir -p /var/lib/rs-surface /var/log/rs-surface /run/rs-surface /mnt/topological-storage
export RS_SURFACE_PROFILE="${RS_SURFACE_PROFILE:-/etc/rs-surface/node.json}"
export RS_SURFACE_STATE="${RS_SURFACE_STATE:-/var/lib/rs-surface}"
export RS_SURFACE_MOUNT="${RS_SURFACE_MOUNT:-/mnt/topological-storage}"
export RS_SURFACE_HOST="${RS_SURFACE_HOST:-0.0.0.0}"
export RS_SURFACE_PORT="${RS_SURFACE_PORT:-8080}"
exec python3 /opt/rs-surface/server.py
EOF
  fi

  cat > "$APKOVL_DIR/root/etc/init.d/rs-surface" <<'EOF'
#!/sbin/openrc-run
name="Research Stack QEMU rs-surface smoke"
description="Disposable QEMU smoke for the Alpine embedded surface"
supervisor=supervise-daemon
command="/bin/sh"
command_args="/opt/rs-surface/boot-rs-surface.sh"
pidfile="/run/rs-surface/rs-surface.pid"
output_log="/var/log/rs-surface/stdout.log"
error_log="/var/log/rs-surface/stderr.log"
respawn_delay=2
respawn_max=2

depend() {
	need net
	after firewall
}

start_pre() {
	mkdir -p /run/rs-surface /var/lib/rs-surface /var/log/rs-surface /mnt/topological-storage
}
EOF

  chmod 0755 \
    "$APKOVL_DIR/root/opt/rs-surface/boot-rs-surface.sh" \
    "$APKOVL_DIR/root/etc/init.d/rs-surface"
  ln -s /etc/init.d/rs-surface "$APKOVL_DIR/root/etc/runlevels/default/rs-surface"
  (cd "$APKOVL_DIR/root" && tar -czf ../rs.apkovl.tar.gz .)
}

cleanup() {
  if [ -s "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      sleep 1
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$PID_FILE"
  fi
}

write_receipt() {
  ok="$1"
  reason="$2"
  python3 - "$RECEIPT" "$ok" "$reason" "$HOST_PORT" "$SERIAL_LOG" <<'PY'
import json, sys, time
from pathlib import Path

path = Path(sys.argv[1])
ok = sys.argv[2] == "true"
serial = Path(sys.argv[5])
tail = ""
if serial.exists():
    data = serial.read_text(errors="replace")
    tail = "\n".join(data.splitlines()[-80:])
receipt = {
    "ok": ok,
    "reason": sys.argv[3],
    "checked_at": time.time(),
    "host_url": f"http://127.0.0.1:{sys.argv[4]}/health",
    "serial_log": str(serial),
    "serial_tail": tail,
}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(path)
PY
}

need curl
need qemu-system-x86_64
need tar
need python3

fetch_asset vmlinuz-virt
fetch_asset initramfs-virt
fetch_asset modloop-virt
build_apkovl
cleanup
trap cleanup EXIT INT TERM

rm -f "$SERIAL_LOG" "$RECEIPT"

qemu-system-x86_64 \
  -machine accel=tcg,type=q35 \
  -cpu max \
  -m "$MEMORY_MB" \
  -smp 1 \
  -nographic \
  -no-reboot \
  -kernel "$ASSET_DIR/vmlinuz-virt" \
  -initrd "$ASSET_DIR/initramfs-virt" \
  -append "console=ttyS0 modules=loop,squashfs,sd-mod,virtio_net,virtio_pci,virtio_blk ip=dhcp alpine_repo=$ALPINE_REPO_URL modloop=$ALPINE_BASE_URL/modloop-virt apkovl=/dev/vda1:vfat:rs.apkovl.tar.gz pkgs=$BOOT_PKGS" \
  -drive "file=fat:rw:$APKOVL_DIR,format=raw,if=virtio" \
  -netdev "user,id=net0,hostfwd=tcp:127.0.0.1:$HOST_PORT-:$GUEST_PORT" \
  -device virtio-net-pci,netdev=net0 \
  -serial "file:$SERIAL_LOG" \
  -monitor none \
  >/dev/null 2>&1 &

echo "$!" > "$PID_FILE"

deadline=$(( $(date +%s) + TIMEOUT_SECONDS ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if curl -fsS "http://127.0.0.1:$HOST_PORT/health" >/tmp/rs-surface-qemu-health.json 2>/dev/null; then
    python3 - "$RECEIPT" "$HOST_PORT" "$SERIAL_LOG" /tmp/rs-surface-qemu-health.json <<'PY'
import json, sys, time
from pathlib import Path

receipt = {
    "ok": True,
    "checked_at": time.time(),
    "host_url": f"http://127.0.0.1:{sys.argv[2]}/health",
    "health": json.loads(Path(sys.argv[4]).read_text()),
    "serial_log": sys.argv[3],
}
Path(sys.argv[1]).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(sys.argv[1])
PY
    cat "$RECEIPT"
    exit 0
  fi
  sleep 2
done

write_receipt false "timeout waiting for forwarded /health"
cat "$RECEIPT"
exit 1
