#!/bin/bash
# restic.sh — restic snapshot status probe (runs only on qfox-1)
# Output: JSON with snapshot count, latest timestamp, repo stats.

RESTIC_BIN=""
for p in /usr/bin/restic /usr/local/bin/restic; do
    if [ -x "$p" ]; then
        RESTIC_BIN="$p"
        break
    fi
done

if [ -z "$RESTIC_BIN" ]; then
    echo '{"restic_installed":false,"error":"restic binary not found"}'
    exit 0
fi

# Load credentials from env file
if [ -f /etc/garage/garage.env ]; then
    set -a
    source /etc/garage/garage.env
    if [ -n "$GARAGE_ACCESS_KEY_ID" ]; then
        export AWS_ACCESS_KEY_ID="$GARAGE_ACCESS_KEY_ID"
        export AWS_SECRET_ACCESS_KEY="$GARAGE_SECRET_ACCESS_KEY"
    fi
    set +a
fi

AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-$GARAGE_ACCESS_KEY_ID}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-$GARAGE_SECRET_ACCESS_KEY}"
RESTIC_REPOSITORY="${RESTIC_REPOSITORY:-s3:http://localhost:3900/research-stack}"
RESTIC_PASSWORD_FILE="${RESTIC_PASSWORD_FILE:-/etc/garage/restic-password}"

export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY RESTIC_REPOSITORY RESTIC_PASSWORD_FILE

# Quick check: is the repo reachable?
repo_check=$("$RESTIC_BIN" snapshots --json --last 2>&1 || true)
if echo "$repo_check" | grep -qi "Is there a repository at the given location"; then
    echo '{"restic_installed":true,"restic_reachable":false,"error":"repository not found or unreachable"}'
    exit 0
fi

# Count snapshots
snapshot_count=0
latest_ts=""
latest_age_hours=0

snapshots_json=$("$RESTIC_BIN" snapshots --json 2>/dev/null || echo "[]")
snapshot_count=$(echo "$snapshots_json" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo 0)

if [ "$snapshot_count" -gt 0 ]; then
    # Get latest timestamp: last entry in the list (or sort and take last)
    latest_ts=$(echo "$snapshots_json" | python3 -c "
import sys, json
snaps = json.load(sys.stdin)
times = [s.get('time','') for s in snaps if s.get('time')]
times.sort()
print(times[-1])" 2>/dev/null || echo "")

    # Calculate age in hours from ISO timestamp
    if [ -n "$latest_ts" ]; then
        now_epoch=$(date +%s)
        ts_epoch=$(date -d "$latest_ts" +%s 2>/dev/null || echo 0)
        if [ "$ts_epoch" -gt 0 ]; then
            latest_age_hours=$(( (now_epoch - ts_epoch) / 3600 ))
        fi
    fi
fi

# Stats: get total size for dedup ratio
stats_json=$("$RESTIC_BIN" stats --json 2>/dev/null || echo "{}")
total_size=$(echo "$stats_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_size',0))" 2>/dev/null || echo 0)
file_size=$(echo "$stats_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_file_size',0))" 2>/dev/null || echo 0)

# Last backup log status
backup_log_ok=false
backup_log_ts=""
backup_log_path="/home/allaun/.cache/restic-backup.log"
if [ -f "$backup_log_path" ]; then
    last_line=$(tail -20 "$backup_log_path" | grep -i "snapshot.*saved" | tail -1 || true)
    if [ -n "$last_line" ]; then
        backup_log_ok=true
        backup_log_ts=$(echo "$last_line" | head -c 20)
    fi
fi

printf '{"restic_installed":true,"restic_reachable":true,"snapshot_count":%s,"latest_ts":"%s","latest_age_hours":%s,"total_size":%s,"file_size":%s,"backup_log_ok":%s}\n' \
    "$snapshot_count" "$latest_ts" "$latest_age_hours" "$total_size" "$file_size" "$backup_log_ok"
