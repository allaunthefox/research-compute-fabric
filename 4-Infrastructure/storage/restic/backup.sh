#!/usr/bin/env bash
# backup.sh — unified backup entrypoint
#
# Orchestrates restic + Garage + rclone in their correct roles:
#
#   restic  → deduplicated encrypted snapshots → Garage (primary repo)
#   rclone  → cold copy of restic repo chunks → gdrive:restic-mirror/
#   rclone  → sync gdrive:research-stack → Garage:gdrive-mirror
#
# Commands:
#   backup.sh snap      [tag]    — restic snapshot of repo + config (default tag: manual)
#   backup.sh snap-db   [dir]    — restic snapshot of SQLite scratch DBs
#   backup.sh snap-rds  <table>  — pg_dump | zstd → restic backup → Garage:rds-overflow
#   backup.sh cold-copy          — rclone copy Garage restic chunks → gdrive cold mirror
#   backup.sh sync-gdrive        — rclone sync gdrive:research-stack → Garage:gdrive-mirror
#   backup.sh verify             — restic check --read-data-subset=5%
#   backup.sh snapshots          — list all restic snapshots
#   backup.sh restore <id> <dst> — restic restore snapshot to directory
#   backup.sh forget             — apply retention policy (keep 7 daily, 4 weekly, 6 monthly)
#   backup.sh full               — snap + cold-copy + sync-gdrive + forget

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../" && pwd)"

# ── Load credentials ───────────────────────────────────────────────────────────
if [ -f "${SCRIPT_DIR}/restic.env" ]; then
    set -a; source "${SCRIPT_DIR}/restic.env"; set +a
elif [ -f /etc/garage/garage.env ]; then
    set -a; source /etc/garage/garage.env; set +a
    AWS_ACCESS_KEY_ID="${GARAGE_ACCESS_KEY_ID:-}"
    AWS_SECRET_ACCESS_KEY="${GARAGE_SECRET_ACCESS_KEY:-}"
fi
: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY not set — source restic.env first}"
: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE not set}"
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION
export RESTIC_REPOSITORY RESTIC_PASSWORD_FILE

RDS_HOST="${RDS_HOST:-database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com}"
RDS_PORT="${RDS_PORT:-5432}"
RDS_USER="${RDS_USER:-postgres}"
RDS_DB="${RDS_DB:-postgres}"

LOG="${HOME}/.cache/restic-backup.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "[backup] $(date +%H:%M:%S)  $*" | tee -a "$LOG" >&2; }

# ── snap: restic backup of the repo tree ──────────────────────────────────────
cmd_snap() {
    local tag="${1:-manual}"
    log "Snapshotting repo → ${RESTIC_REPOSITORY}  [tag:${tag}]"
    restic backup \
        "${REPO_ROOT}" \
        --tag "${tag}" \
        --exclude ".git/objects" \
        --exclude ".git/lfs" \
        --exclude ".lake/" \
        --exclude "lake-packages/" \
        --exclude "__pycache__/" \
        --exclude "*.pyc" \
        --exclude "node_modules/" \
        --exclude ".venv/" \
        --exclude "venv/" \
        --exclude "*.iso" \
        --exclude "containers/" \
        --exclude ".local/share/containers/" \
        --one-file-system \
        2>&1 | tee -a "$LOG"
    log "Snapshot complete."
}

# ── snap-db: SQLite scratch DBs ───────────────────────────────────────────────
cmd_snap_db() {
    local src_dir="${1:-${REPO_ROOT}}"
    log "Snapshotting SQLite DBs in ${src_dir}..."

    # Collect all SQLite files into a temp manifest
    local tmpdir
    tmpdir="$(mktemp -d /tmp/restic-db-XXXX)"

    find "${src_dir}" -maxdepth 5 \
        \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) \
        -not -path "*/.git/*" -not -path "*/.lake/*" \
        -not -path "*/node_modules/*" \
        -print0 2>/dev/null \
        | while IFS= read -r -d '' f; do
            # Hard-link into tmpdir to give restic a stable tree
            local dest="${tmpdir}${f}"
            mkdir -p "$(dirname "$dest")"
            ln "$f" "$dest" 2>/dev/null || cp "$f" "$dest"
        done

    local count
    count=$(find "$tmpdir" -type f | wc -l)
    log "  ${count} SQLite file(s) found"

    if [ "$count" -gt 0 ]; then
        restic backup "${tmpdir}" \
            --tag "db-scratch" \
            --host "$(hostname -s)" \
            2>&1 | tee -a "$LOG"
    fi

    rm -rf "$tmpdir"
    log "SQLite snapshot done."
}

# ── snap-rds: stream pg_dump through restic (no temp file on disk) ────────────
cmd_snap_rds() {
    local table="${1:?Usage: $0 snap-rds <table> [schema]}"
    local schema="${2:-public}"
    local ts
    ts="$(date +%Y%m%dT%H%M%S)"
    local tag="rds-${schema}.${table}"

    log "Streaming pg_dump ${schema}.${table} → restic [tag:${tag}]..."

    # restic backup --stdin reads from stdin and stores as a virtual file
    PGPASSWORD="${RDS_PASSWORD:-}" pg_dump \
        -h "${RDS_HOST}" -p "${RDS_PORT}" -U "${RDS_USER}" -d "${RDS_DB}" \
        --table="${schema}.${table}" \
        --no-owner --no-privileges \
        | zstd -3 -T0 \
        | restic backup \
            --stdin \
            --stdin-filename "${schema}.${table}.${ts}.sql.zst" \
            --tag "${tag}" \
            2>&1 | tee -a "$LOG"

    log "RDS snapshot done."
}

# ── cold-copy: rclone mirrors restic repo chunks to gdrive ────────────────────
cmd_cold_copy() {
    log "Cold-copying restic repo chunks: Garage → gdrive:restic-mirror/"

    # Build a temporary rclone config that speaks to Garage
    local tmpconf
    tmpconf="$(mktemp /tmp/rclone-garage-XXXX.conf)"
    cat > "$tmpconf" << RCONF
[garage_s3]
type = s3
provider = Other
endpoint = ${AWS_ENDPOINT_URL:-http://localhost:3900}
access_key_id = ${AWS_ACCESS_KEY_ID}
secret_access_key = ${AWS_SECRET_ACCESS_KEY}
region = ${AWS_DEFAULT_REGION:-garage}
force_path_style = true
no_check_bucket = true
RCONF

    # rclone copies Garage:research-stack → gdrive:restic-mirror
    # Uses rclone's own rate-limiting for the gdrive side
    rclone copy \
        "garage_s3:research-stack" \
        "gdrive:restic-mirror" \
        --config "${tmpconf}" \
        --transfers 4 \
        --checkers 8 \
        --drive-pacer-min-sleep 200ms \
        --drive-pacer-burst 10 \
        --retries 10 \
        --retries-sleep 1s \
        --stats 30s \
        --log-level INFO \
        2>&1 | tee -a "$LOG"

    rm -f "$tmpconf"
    log "Cold copy complete — restic repo mirrored to gdrive:restic-mirror/"
}

# ── sync-gdrive: rclone mirrors gdrive project folder → Garage ───────────────
cmd_sync_gdrive() {
    log "Syncing gdrive:research-stack → Garage:gdrive-mirror..."

    local tmpconf
    tmpconf="$(mktemp /tmp/rclone-garage-XXXX.conf)"
    cat > "$tmpconf" << RCONF
[garage_s3]
type = s3
provider = Other
endpoint = ${AWS_ENDPOINT_URL:-http://localhost:3900}
access_key_id = ${AWS_ACCESS_KEY_ID}
secret_access_key = ${AWS_SECRET_ACCESS_KEY}
region = ${AWS_DEFAULT_REGION:-garage}
force_path_style = true
no_check_bucket = true
RCONF

    rclone sync \
        "gdrive:research-stack" \
        "garage_s3:gdrive-mirror" \
        --config "${tmpconf}" \
        --transfers 4 \
        --drive-pacer-min-sleep 200ms \
        --drive-pacer-burst 10 \
        --retries 10 \
        --retries-sleep 1s \
        --exclude "*.iso" \
        --exclude "**/node_modules/**" \
        --stats 30s \
        --log-level INFO \
        2>&1 | tee -a "$LOG"

    rm -f "$tmpconf"
    log "gdrive sync complete."
}

# ── forget: retention policy ──────────────────────────────────────────────────
cmd_forget() {
    log "Applying retention policy..."
    restic forget \
        --keep-last 3 \
        --keep-daily 7 \
        --keep-weekly 4 \
        --keep-monthly 6 \
        --prune \
        2>&1 | tee -a "$LOG"
    log "Retention policy applied."
}

# ── verify: spot-check repo integrity ─────────────────────────────────────────
cmd_verify() {
    log "Verifying restic repo (5% data sample)..."
    restic check --read-data-subset=5% 2>&1 | tee -a "$LOG"
}

# ── snapshots: list ───────────────────────────────────────────────────────────
cmd_snapshots() {
    restic snapshots --compact 2>&1
}

# ── restore ───────────────────────────────────────────────────────────────────
cmd_restore() {
    local snap_id="${1:?Usage: $0 restore <snapshot-id|latest> <target-dir>}"
    local target="${2:?Usage: $0 restore <snapshot-id|latest> <target-dir>}"
    log "Restoring snapshot ${snap_id} → ${target}..."
    restic restore "${snap_id}" --target "${target}" 2>&1 | tee -a "$LOG"
    log "Restore complete."
}

# ── full: everything in one pass ─────────────────────────────────────────────
cmd_full() {
    log "=== Full backup pass ==="
    cmd_snap "scheduled"
    cmd_snap_db "${REPO_ROOT}"
    cmd_cold_copy
    cmd_sync_gdrive
    cmd_forget
    log "=== Full backup pass complete ==="
}

# ── dispatch ───────────────────────────────────────────────────────────────────
CMD="${1:-snapshots}"
shift || true
case "$CMD" in
    snap)         cmd_snap "$@" ;;
    snap-db)      cmd_snap_db "$@" ;;
    snap-rds)     cmd_snap_rds "$@" ;;
    cold-copy)    cmd_cold_copy ;;
    sync-gdrive)  cmd_sync_gdrive ;;
    forget)       cmd_forget ;;
    verify)       cmd_verify ;;
    snapshots)    cmd_snapshots ;;
    restore)      cmd_restore "$@" ;;
    full)         cmd_full ;;
    *)
        echo "Usage: $0 {snap|snap-db|snap-rds|cold-copy|sync-gdrive|forget|verify|snapshots|restore|full}" >&2
        exit 1 ;;
esac
