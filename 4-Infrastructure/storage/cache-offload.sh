#!/usr/bin/env bash
# cache-offload.sh
#
# Three-tier cache offload for database work.
#
# Tier 0  /mnt/stackcache  (local ZFS, hot scratch — created by zfs-pool-setup.sh)
# Tier 1  node_<hostname>: (rclone SFTP to Tailscale nodes — added by add-node-remote.sh)
# Tier 2  gdrive:research-stack-offload  (cold overflow)
#
# What it offloads:
#   A. SQLite scratch databases (*.db, *.sqlite, *.sqlite3) from a source dir
#   B. Aurora RDS table exports via pg_dump / COPY TO → compressed .sql.zst
#
# Offload routing:
#   File < TIER1_THRESHOLD (default 2 GB) → nearest online Tier 1 node
#   File ≥ TIER1_THRESHOLD OR no Tier 1 available → Tier 2 (gdrive)
#   All offloads also write a JSON manifest entry to track location.
#
# Usage:
#   cache-offload.sh sqlite <source-dir>            # offload SQLite files
#   cache-offload.sh rds    <table> [schema]        # offload RDS table
#   cache-offload.sh status                          # show tier usage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${SCRIPT_DIR}/node-registry.json"
MANIFEST="${SCRIPT_DIR}/offload-manifest.json"

TIER0_DB="/mnt/stackcache/db"
TIER0_PGDUMP="/mnt/stackcache/pgdump"
TIER2_REMOTE="gdrive:research-stack-offload"
TIER1_THRESHOLD_GB=2

RDS_HOST="${RDS_HOST:-database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com}"
RDS_PORT="${RDS_PORT:-5432}"
RDS_USER="${RDS_USER:-postgres}"
RDS_DB="${RDS_DB:-postgres}"

# ── Helpers ────────────────────────────────────────────────────────────────────

log() { echo "[cache-offload] $*" >&2; }

file_size_gb() {
    local f="$1"
    python3 -c "import os; print(os.path.getsize('${f}') / 1073741824)"
}

# Find the best online Tier 1 node (most free space, reachable)
best_tier1_remote() {
    [ ! -f "$REGISTRY" ] && return 1
    python3 - << 'PYEOF'
import json, subprocess, sys

with open("${REGISTRY}") as f:
    nodes = json.load(f)

best = None
best_avail = 0
for node in nodes:
    remote = node["rclone_remote"]
    try:
        result = subprocess.run(
            ["rclone", "about", f"{remote}:", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            avail = info.get("free", 0)
            if avail > best_avail:
                best_avail = avail
                best = remote
    except Exception:
        continue

if best:
    print(best)
    sys.exit(0)
sys.exit(1)
PYEOF
}

manifest_add() {
    local src="$1" dest="$2" tier="$3" sha256="$4"
    python3 - << PYEOF
import json, os
from datetime import datetime, timezone

path = "${MANIFEST}"
entries = []
if os.path.exists(path):
    with open(path) as f:
        entries = json.load(f)
entries.append({
    "src": "${src}",
    "dest": "${dest}",
    "tier": ${tier},
    "sha256": "${sha256}",
    "offloaded_at": datetime.now(timezone.utc).isoformat(),
    "status": "offloaded"
})
with open(path, "w") as f:
    json.dump(entries, f, indent=2)
PYEOF
}

# ── Tier 0 check ──────────────────────────────────────────────────────────────
tier0_available() {
    [ -d "$TIER0_DB" ] && return 0
    log "WARNING: Tier 0 ZFS not mounted at /mnt/stackcache — run zfs-pool-setup.sh"
    return 1
}

# ── SQLite offload ─────────────────────────────────────────────────────────────
cmd_sqlite() {
    local src_dir="${1:?Usage: $0 sqlite <source-dir>}"
    log "Scanning ${src_dir} for SQLite files..."

    find "${src_dir}" -maxdepth 4 \
        \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) \
        -not -path "*/\.*" \
        | while read -r db_file; do

        local size_gb fname sha256 dest_remote dest_path tier
        fname="$(basename "${db_file}")"
        sha256="$(sha256sum "${db_file}" | awk '{print $1}')"
        size_gb="$(file_size_gb "${db_file}")"

        log "  ${fname}  (${size_gb} GB)"

        # Copy to Tier 0 first (ZFS, fast)
        if tier0_available; then
            rsync -a --inplace "${db_file}" "${TIER0_DB}/${fname}"
            log "  → Tier 0: ${TIER0_DB}/${fname}"
        fi

        # Route to Tier 1 or Tier 2
        if python3 -c "exit(0 if ${size_gb} < ${TIER1_THRESHOLD_GB} else 1)"; then
            dest_remote="$(best_tier1_remote 2>/dev/null || true)"
        fi

        if [ -n "${dest_remote:-}" ]; then
            tier=1
            dest_path="${dest_remote}:db/${fname}"
            log "  → Tier 1: ${dest_path}"
            rclone copyto "${db_file}" "${dest_path}" \
                --drive-pacer-min-sleep 200ms \
                --drive-pacer-burst 10 \
                --retries 5
        else
            tier=2
            dest_path="${TIER2_REMOTE}/db/${fname}"
            log "  → Tier 2: ${dest_path} (gdrive)"
            rclone copyto "${db_file}" "${dest_path}" \
                --drive-pacer-min-sleep 200ms \
                --drive-pacer-burst 10 \
                --retries 10 \
                --retries-sleep 1s
        fi

        manifest_add "${db_file}" "${dest_path}" "${tier}" "${sha256}"
    done

    log "SQLite offload complete."
}

# ── RDS table offload ──────────────────────────────────────────────────────────
cmd_rds() {
    local table="${1:?Usage: $0 rds <table> [schema]}"
    local schema="${2:-public}"
    local ts
    ts="$(date +%Y%m%d_%H%M%S)"
    local dump_name="${schema}.${table}.${ts}.sql.zst"

    log "Dumping ${schema}.${table} from RDS..."

    if tier0_available; then
        local dump_path="${TIER0_PGDUMP}/${dump_name}"
    else
        local dump_path="/tmp/${dump_name}"
    fi

    # pg_dump piped through zstd compression — no uncompressed file on disk
    PGPASSWORD="${RDS_PASSWORD:-}" pg_dump \
        -h "${RDS_HOST}" -p "${RDS_PORT}" -U "${RDS_USER}" -d "${RDS_DB}" \
        --table="${schema}.${table}" \
        --no-owner --no-privileges \
        | zstd -9 -T0 -o "${dump_path}"

    local size_gb sha256 dest_remote dest_path tier
    sha256="$(sha256sum "${dump_path}" | awk '{print $1}')"
    size_gb="$(file_size_gb "${dump_path}")"
    log "  Dump: ${dump_path} (${size_gb} GB)"

    if python3 -c "exit(0 if ${size_gb} < ${TIER1_THRESHOLD_GB} else 1)"; then
        dest_remote="$(best_tier1_remote 2>/dev/null || true)"
    fi

    if [ -n "${dest_remote:-}" ]; then
        tier=1
        dest_path="${dest_remote}:pgdump/${dump_name}"
        log "  → Tier 1: ${dest_path}"
        rclone copyto "${dump_path}" "${dest_path}" --retries 5
    else
        tier=2
        dest_path="${TIER2_REMOTE}/pgdump/${dump_name}"
        log "  → Tier 2: ${dest_path} (gdrive)"
        rclone copyto "${dump_path}" "${dest_path}" \
            --drive-pacer-min-sleep 200ms \
            --drive-pacer-burst 10 \
            --retries 10 \
            --retries-sleep 1s
    fi

    manifest_add "${dump_path}" "${dest_path}" "${tier}" "${sha256}"
    log "RDS offload complete: ${dest_path}"
}

# ── Status ────────────────────────────────────────────────────────────────────
cmd_status() {
    echo "=== Tier 0: Local ZFS ==="
    if [ -d /mnt/stackcache ]; then
        df -h /mnt/stackcache 2>/dev/null || true
        zfs list -r stackcache 2>/dev/null || true
    else
        echo "  Not mounted (run zfs-pool-setup.sh after rebooting into 7.0.9 kernel)"
    fi

    echo ""
    echo "=== Tier 1: Node remotes ==="
    if [ -f "$REGISTRY" ]; then
        python3 -c "
import json
with open('${REGISTRY}') as f:
    nodes = json.load(f)
for n in nodes:
    print(f\"  {n['rclone_remote']:30s}  {n['tailscale_ip']}  {n['cache_path']}\")
"
    else
        echo "  No nodes registered yet (run add-node-remote.sh)"
    fi

    echo ""
    echo "=== Tier 2: gdrive ==="
    rclone size "${TIER2_REMOTE}" 2>/dev/null || echo "  (not yet populated)"

    echo ""
    echo "=== Offload manifest ==="
    if [ -f "$MANIFEST" ]; then
        python3 -c "
import json
with open('${MANIFEST}') as f:
    entries = json.load(f)
print(f'  {len(entries)} entries')
by_tier = {}
for e in entries:
    t = e.get('tier',0)
    by_tier[t] = by_tier.get(t,0) + 1
for t,n in sorted(by_tier.items()):
    print(f'  Tier {t}: {n} files')
"
    else
        echo "  Empty"
    fi
}

# ── Dispatch ───────────────────────────────────────────────────────────────────
CMD="${1:-status}"
shift || true
case "$CMD" in
    sqlite) cmd_sqlite "$@" ;;
    rds)    cmd_rds    "$@" ;;
    status) cmd_status       ;;
    *) echo "Usage: $0 {sqlite <dir>|rds <table> [schema]|status}" >&2; exit 1 ;;
esac
