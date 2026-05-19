#!/usr/bin/env bash
# db-consolidate.sh
#
# Offloads active database work to Garage (S3) and consolidates static data
# back to Aurora RDS. Called by the git post-commit hook and can be run manually.
#
# Two modes:
#   offload    — push hot SQLite scratch DBs + RDS overflow dumps → Garage S3
#   consolidate — pull static data from Garage db-scratch/rds-overflow → RDS
#
# Garage buckets:
#   db-scratch    — SQLite scratch databases (active work)
#   rds-overflow  — pg_dump / COPY TO exports too large for RDS hot storage
#   research-stack — primary project objects
#   gdrive-mirror  — sync point for gdrive:research-stack
#   snap-zone     — ZFS send/receive snapshots
#
# "Static" detection: a file is static if it hasn't been modified in
# STATIC_THRESHOLD_MINUTES (default 60) minutes.
#
# Usage:
#   db-consolidate.sh offload   [source-dir]     # default: current repo root
#   db-consolidate.sh consolidate                 # pull static → RDS
#   db-consolidate.sh status                      # show what's in Garage
#   db-consolidate.sh sync-gdrive                 # mirror gdrive → garage bucket
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Garage credentials (source /etc/garage/garage.env if not already set) ─────
if [ -z "${AWS_ACCESS_KEY_ID:-}" ] && [ -f /etc/garage/garage.env ]; then
    set -a; source /etc/garage/garage.env; set +a
    AWS_ACCESS_KEY_ID="${GARAGE_ACCESS_KEY_ID:-$AWS_ACCESS_KEY_ID}"
    AWS_SECRET_ACCESS_KEY="${GARAGE_SECRET_ACCESS_KEY:-$AWS_SECRET_ACCESS_KEY}"
fi
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-garage}"
export AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:3900}"

RDS_HOST="${RDS_HOST:-database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com}"
RDS_PORT="${RDS_PORT:-5432}"
RDS_USER="${RDS_USER:-postgres}"
RDS_DB="${RDS_DB:-postgres}"
STATIC_THRESHOLD_MINUTES="${STATIC_THRESHOLD_MINUTES:-60}"

S3="aws s3 --endpoint-url ${AWS_ENDPOINT_URL}"

log() { echo "[db-consolidate] $(date +%H:%M:%S)  $*" >&2; }

s3_cp() {
    aws s3 cp --endpoint-url "${AWS_ENDPOINT_URL}" "$@" 2>&1
}
s3_ls() {
    aws s3 ls --endpoint-url "${AWS_ENDPOINT_URL}" "$@" 2>&1
}

# ── offload ────────────────────────────────────────────────────────────────────
cmd_offload() {
    local src_dir="${1:-$REPO_ROOT}"
    log "Scanning ${src_dir} for SQLite files..."

    local count=0
    while IFS= read -r -d '' db_file; do
        local fname sha256
        fname="$(basename "${db_file}")"
        sha256="$(sha256sum "${db_file}" | awk '{print $1}')"
        local ts
        ts="$(date +%Y%m%dT%H%M%S)"
        local key="$(hostname -s)/${ts}/${fname}"

        log "  → s3://db-scratch/${key}"
        s3_cp "${db_file}" "s3://db-scratch/${key}" \
            --metadata "sha256=${sha256},source=${db_file}" \
            --storage-class STANDARD
        (( count++ )) || true
    done < <(find "${src_dir}" -maxdepth 5 \
        \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) \
        -not -path "*/.git/*" \
        -not -path "*/.lake/*" \
        -not -path "*/node_modules/*" \
        -print0 2>/dev/null)

    log "Offloaded ${count} SQLite file(s) to s3://db-scratch/"
}

# ── rds-dump ───────────────────────────────────────────────────────────────────
cmd_rds_dump() {
    local table="${1:?Usage: $0 rds-dump <table> [schema]}"
    local schema="${2:-public}"
    local ts
    ts="$(date +%Y%m%dT%H%M%S)"
    local key="$(hostname -s)/${ts}/${schema}.${table}.sql.zst"
    local tmp="/tmp/garage-rds-dump-$$.sql.zst"

    log "Dumping ${schema}.${table} → s3://rds-overflow/${key}"
    PGPASSWORD="${RDS_PASSWORD:-}" pg_dump \
        -h "${RDS_HOST}" -p "${RDS_PORT}" -U "${RDS_USER}" -d "${RDS_DB}" \
        --table="${schema}.${table}" \
        --no-owner --no-privileges \
        | zstd -9 -T0 -o "${tmp}"

    s3_cp "${tmp}" "s3://rds-overflow/${key}" \
        --metadata "table=${schema}.${table},host=${RDS_HOST}"
    rm -f "${tmp}"
    log "Done: s3://rds-overflow/${key}"
}

# ── consolidate ────────────────────────────────────────────────────────────────
cmd_consolidate() {
    log "Looking for static objects in s3://db-scratch/ and s3://rds-overflow/ ..."

    local now_epoch
    now_epoch=$(date +%s)
    local threshold_secs=$(( STATIC_THRESHOLD_MINUTES * 60 ))

    # db-scratch: static SQLite files → restore locally (they're scratch, don't push to RDS)
    log "--- db-scratch (static files only) ---"
    s3_ls "s3://db-scratch/" --recursive 2>/dev/null | while read -r date time size key; do
        # Parse S3 date+time as epoch
        local mod_epoch
        mod_epoch=$(date -d "${date} ${time}" +%s 2>/dev/null || echo 0)
        local age=$(( now_epoch - mod_epoch ))
        if [ "$age" -gt "$threshold_secs" ]; then
            local fname
            fname="$(basename "${key}")"
            log "  Static (${age}s old): ${key}"
            # Tag as consolidated — Garage doesn't have lifecycle but we track it
            aws s3api put-object-tagging \
                --endpoint-url "${AWS_ENDPOINT_URL}" \
                --bucket db-scratch \
                --key "${key}" \
                --tagging '{"TagSet":[{"Key":"status","Value":"static"}]}' 2>/dev/null || true
        fi
    done

    # rds-overflow: static dumps → restore into RDS
    log "--- rds-overflow → RDS restore ---"
    s3_ls "s3://rds-overflow/" --recursive 2>/dev/null | while read -r date time size key; do
        local mod_epoch
        mod_epoch=$(date -d "${date} ${time}" +%s 2>/dev/null || echo 0)
        local age=$(( now_epoch - mod_epoch ))
        if [ "$age" -gt "$threshold_secs" ]; then
            log "  Consolidating ${key} → RDS..."
            local tmp="/tmp/garage-consolidate-$$.sql.zst"
            s3_cp "s3://rds-overflow/${key}" "${tmp}" --quiet
            # Decompress and restore
            zstd -d -T0 "${tmp}" --stdout \
                | PGPASSWORD="${RDS_PASSWORD:-}" psql \
                    -h "${RDS_HOST}" -p "${RDS_PORT}" -U "${RDS_USER}" -d "${RDS_DB}" \
                    --quiet 2>&1
            rm -f "${tmp}"
            # Tag as consolidated
            aws s3api put-object-tagging \
                --endpoint-url "${AWS_ENDPOINT_URL}" \
                --bucket rds-overflow \
                --key "${key}" \
                --tagging '{"TagSet":[{"Key":"status","Value":"consolidated"}]}' 2>/dev/null || true
            log "  Done: ${key}"
        fi
    done

    log "Consolidation pass complete."
}

# ── sync-gdrive ────────────────────────────────────────────────────────────────
cmd_sync_gdrive() {
    # Mirror from gdrive (mounted at /home/allaun/gdrive or via rclone) into
    # the Garage gdrive-mirror bucket. Rate limits respected (rclone pacer).
    log "Syncing gdrive:research-stack → s3://gdrive-mirror/ via rclone..."

    GDRIVE_MOUNT="/home/allaun/gdrive/research-stack"
    if [ ! -d "${GDRIVE_MOUNT}" ]; then
        log "  gdrive not mounted at ${GDRIVE_MOUNT} — mounting..."
        mkdir -p "${GDRIVE_MOUNT}"
        rclone mount gdrive:research-stack "${GDRIVE_MOUNT}" \
            --daemon \
            --vfs-cache-mode minimal \
            --dir-cache-time 10m \
            --drive-pacer-min-sleep 200ms \
            --drive-pacer-burst 10
        sleep 3
    fi

    # Use rclone to copy into Garage (rclone speaks S3)
    RCLONE_CONFIG_CONTENT="
[garage]
type = s3
provider = Other
endpoint = ${AWS_ENDPOINT_URL}
access_key_id = ${AWS_ACCESS_KEY_ID}
secret_access_key = ${AWS_SECRET_ACCESS_KEY}
region = garage
force_path_style = true
"
    TMPCONF="$(mktemp /tmp/rclone-garage-XXXX.conf)"
    echo "${RCLONE_CONFIG_CONTENT}" > "${TMPCONF}"

    rclone sync "${GDRIVE_MOUNT}" "garage:gdrive-mirror" \
        --config "${TMPCONF}" \
        --transfers 4 \
        --checkers 8 \
        --retries 5 \
        --exclude ".git/**" \
        --exclude "*.iso" \
        --exclude "**/node_modules/**" \
        --stats 30s \
        --log-level INFO 2>&1

    rm -f "${TMPCONF}"
    log "gdrive sync complete."
}

# ── status ─────────────────────────────────────────────────────────────────────
cmd_status() {
    echo "=== Garage cluster ==="
    sudo garage -c /etc/garage/garage.toml \
        --admin-token "$(sudo grep GARAGE_ADMIN_TOKEN /etc/garage/garage.env | cut -d= -f2)" \
        status 2>&1

    echo ""
    echo "=== Buckets ==="
    for bucket in research-stack db-scratch rds-overflow snap-zone gdrive-mirror; do
        echo -n "  s3://${bucket}/  "
        s3_ls "s3://${bucket}/" --recursive --summarize 2>/dev/null \
            | grep "Total" | tr '\n' '  ' || echo "(empty or unreachable)"
        echo ""
    done
}

# ── dispatch ───────────────────────────────────────────────────────────────────
CMD="${1:-status}"
shift || true
case "$CMD" in
    offload)      cmd_offload "$@" ;;
    rds-dump)     cmd_rds_dump "$@" ;;
    consolidate)  cmd_consolidate ;;
    sync-gdrive)  cmd_sync_gdrive ;;
    status)       cmd_status ;;
    *)
        echo "Usage: $0 {offload [dir]|rds-dump <table> [schema]|consolidate|sync-gdrive|status}" >&2
        exit 1
        ;;
esac
