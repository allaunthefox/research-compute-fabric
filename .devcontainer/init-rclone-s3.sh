#!/usr/bin/env bash
# init-rclone-s3.sh
#
# Starts rclone as an S3-compatible gateway in front of the gdrive remote.
# Called automatically when the dev container launches (via CMD in Dockerfile).
#
# ── Google Drive API quota limits (as of 2026-05-01) ────────────────────────
#   Per-minute per-project:          1,000,000 quota units
#   Per-minute per-user per-project:   325,000 quota units
#   Per-method costs:
#     files.list  (S3 ListObjects)  = 100 units per call
#     files.get   (S3 HeadObject)   =   5 units per call
#     files.download (S3 GetObject) = 200 units per call
#   → Sustained safe rate: ≤ 10 API calls/second (Google's own guidance)
#   → 403/429 on exceed; rclone uses exponential backoff to recover
#   Source: https://developers.google.com/drive/api/guides/limits
#
# ── How serve s3 touches the Drive API ──────────────────────────────────────
#   Every S3 ListObjects maps to files.list (100 units each).
#   The VFS directory cache (--dir-cache-time) is the primary defence:
#   while the cache is warm, listings are served locally with ZERO API calls.
#   --poll-interval controls how often rclone re-checks Drive for remote
#   changes; set long so background polling doesn't burn quota.
#
# ── Client ID note ──────────────────────────────────────────────────────────
#   rclone's shared client_id is rate-limited across ALL rclone users.
#   For production or sustained use, create your own OAuth client_id:
#   https://rclone.org/drive/#making-your-own-client-id
#   Set RCLONE_DRIVE_CLIENT_ID + RCLONE_DRIVE_CLIENT_SECRET in the
#   environment (or in rclone.conf) to use it.
#
# ── Inside the container ─────────────────────────────────────────────────────
#   S3 endpoint:   http://localhost:9000
#   access_key:    gdrive
#   secret_key:    gdrive
#   region:        us-east-1   (dummy; required by boto3/AWS CLI)
#   Each Drive folder at root level is an S3 bucket, e.g.:
#     s3://research-stack/  → gdrive:research-stack/
#
# Environment overrides (set in devcontainer.json or shell):
#   RCLONE_S3_ADDR   - listen address       (default: :9000)
#   RCLONE_S3_KEY    - "access,secret" pair  (default: gdrive,gdrive)
#   RCLONE_REMOTE    - rclone remote + path  (default: gdrive:)

set -euo pipefail

ADDR="${RCLONE_S3_ADDR:-:9000}"
AUTH_KEY="${RCLONE_S3_KEY:-gdrive,gdrive}"
REMOTE="${RCLONE_REMOTE:-gdrive:}"
LOG_FILE="${HOME}/.cache/rclone-s3.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Wait up to 15 s for the rclone.conf bind-mount to appear (container startup race)
for i in $(seq 1 15); do
    if [ -f "${HOME}/.config/rclone/rclone.conf" ]; then
        break
    fi
    echo "[init-rclone-s3] waiting for rclone.conf mount ($i/15)..." >&2
    sleep 1
done

if [ ! -f "${HOME}/.config/rclone/rclone.conf" ]; then
    echo "[init-rclone-s3] WARNING: rclone.conf not found — gdrive S3 gateway will not start." >&2
    exec "$@"
fi

echo "[init-rclone-s3] starting rclone serve s3 ${REMOTE} on ${ADDR}" >&2

rclone serve s3 "${REMOTE}" \
    --addr "${ADDR}" \
    --auth-key "${AUTH_KEY}" \
    \
    `# ── Rate-limit compliance ─────────────────────────────────────────────` \
    `# Stay well under Google's 10 TPS guidance for the shared client_id.` \
    `# pacer-min-sleep=200ms + pacer-burst=10 caps sustained rate to ~5 TPS.` \
    `# If you use your own client_id (RCLONE_DRIVE_CLIENT_ID) you can relax` \
    `# pacer-burst to 50 and min-sleep to 100ms safely.` \
    --drive-pacer-min-sleep 200ms \
    --drive-pacer-burst 10 \
    \
    `# ── Directory / VFS cache ─────────────────────────────────────────────` \
    `# Warm cache means zero API calls for repeated S3 ListObjects.` \
    `# dir-cache-time=10m: listing is served locally for 10 minutes.` \
    `# poll-interval=5m: rclone checks Drive for remote changes every 5 min.` \
    `# vfs-cache-mode=minimal: only open files are cached locally; reads and` \
    `# writes pass through. Avoids bulk-downloading the whole Drive.` \
    --dir-cache-time 10m \
    --poll-interval 5m \
    --vfs-cache-mode minimal \
    --vfs-cache-max-size 1G \
    --vfs-read-chunk-size 32M \
    --vfs-read-chunk-size-limit 256M \
    \
    `# ── Upload safety ────────────────────────────────────────────────────` \
    `# 750 GB/day upload limit per Google Workspace user.` \
    `# 8 MiB chunk size (Drive default); larger chunks = fewer API round-trips` \
    `# for big files, but each chunk counts as a transaction.` \
    --drive-chunk-size 8M \
    \
    `# ── Reliability ──────────────────────────────────────────────────────` \
    `# retries=10: exponential backoff on 403/429 as Google recommends.` \
    `# low-level-retries=20: retry transient network errors before giving up.` \
    `# retries-sleep=1s: initial backoff delay (doubles each retry).` \
    --retries 10 \
    --retries-sleep 1s \
    --low-level-retries 20 \
    \
    `# ── Logging ──────────────────────────────────────────────────────────` \
    --log-file "${LOG_FILE}" \
    --log-level INFO \
    \
    `# ── Misc ─────────────────────────────────────────────────────────────` \
    `# no-checksum: skip MD5 verification on serve (reduces files.get calls).` \
    --no-checksum \
    &

RCLONE_PID=$!
echo "[init-rclone-s3] rclone serve s3 pid=${RCLONE_PID}" >&2

# Give it a moment to bind before handing off to the main command
sleep 2
if ! kill -0 "${RCLONE_PID}" 2>/dev/null; then
    echo "[init-rclone-s3] ERROR: rclone failed to start — check ${LOG_FILE}" >&2
fi

# Hand off to whatever CMD or command was passed (default: bash)
exec "${@:-/bin/bash}"
