#!/bin/bash
# gdrive_offload.sh — gdrive sync status probe (runs on qfox-1)
# Checks if cold copy is synced, recent offload timestamp.

last_cold_copy_ts="never"
last_cold_copy_epoch=0
now_epoch=$(date +%s)

log_path="/home/allaun/.cache/storage-agent.log"
if [ -f "$log_path" ]; then
    # Look for last successful cold-copy or sync-gdrive mention
    last_line=$(grep -E "(cold-copy|sync-gdrive).*succeeded" "$log_path" 2>/dev/null | tail -1 || true)
    if [ -n "$last_line" ]; then
        # Extract ISO timestamp from last_line (assumes format: YYYY-MM-DD HH:MM:SS,...)
        ts_raw=$(echo "$last_line" | grep -oP '\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')
        if [ -n "$ts_raw" ]; then
            last_cold_copy_ts="$ts_raw"
            last_cold_copy_epoch=$(date -d "$ts_raw" +%s 2>/dev/null || echo 0)
        fi
    fi
fi

hours_since_copy=0
if [ "$last_cold_copy_epoch" -gt 0 ]; then
    hours_since_copy=$(( (now_epoch - last_cold_copy_epoch) / 3600 ))
fi

printf '{"last_cold_copy_ts":"%s","hours_since_copy":%s}\n' "$last_cold_copy_ts" "$hours_since_copy"
