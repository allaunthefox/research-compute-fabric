#!/bin/bash
# system.sh — basic node health probe (disk, mem, load, zram, systemd)
# Output: JSON to stdout. No external dependencies beyond coreutils + procfs.

set -e

HOSTNAME=$(hostname)
DISK_PCT=0
DISK_TOTAL=0
DISK_FREE=0
MEM_PCT=0
MEM_TOTAL=0
MEM_FREE=0
LOAD_1M=0
LOAD_5M=0
LOAD_15M=0
UPTIME=0
ZRAM_USED=0
ZRAM_TOTAL=0

# disk usage on /
disk_info=$(df -k / 2>/dev/null | awk 'NR==2 {print $2, $4, $5}')
if [ -n "$disk_info" ]; then
    DISK_TOTAL=$(echo "$disk_info" | awk '{printf "%.0f", $1/1024}')
    DISK_FREE=$(echo "$disk_info" | awk '{printf "%.0f", $2/1024}')
    DISK_PCT=$(echo "$disk_info" | awk '{print $3}' | tr -d '%')
fi

# memory
mem_info=$(free -m 2>/dev/null | awk 'NR==2 {print $2, $7}')
if [ -n "$mem_info" ]; then
    MEM_TOTAL=$(echo "$mem_info" | awk '{print $1}')
    MEM_FREE=$(echo "$mem_info" | awk '{print $2}')
    if [ "$MEM_TOTAL" -gt 0 ]; then
        used=$((MEM_TOTAL - MEM_FREE))
        MEM_PCT=$((used * 100 / MEM_TOTAL))
    fi
fi

# load average
load_info=$(awk '{print $1, $2, $3}' /proc/loadavg 2>/dev/null)
if [ -n "$load_info" ]; then
    LOAD_1M=$(echo "$load_info" | awk '{printf "%.2f", $1}')
    LOAD_5M=$(echo "$load_info" | awk '{printf "%.2f", $2}')
    LOAD_15M=$(echo "$load_info" | awk '{printf "%.2f", $3}')
fi

# uptime in seconds
UPTIME=$(awk '{printf "%.0f", $1}' /proc/uptime 2>/dev/null || echo 0)

# zram
if command -v zramctl &>/dev/null; then
    zram_info=$(zramctl --output-all --bytes 2>/dev/null | awk -F'[[:space:]]+' 'NR>1 {
        used+=$3; total+=$4
    } END {
        printf "%.0f %.0f", used/1048576, total/1048576
    }')
    if [ -n "$zram_info" ]; then
        ZRAM_USED=$(echo "$zram_info" | awk '{print $1}')
        ZRAM_TOTAL=$(echo "$zram_info" | awk '{print $2}')
    fi
fi

printf '{"node":"%s","hostname":"%s","disk":{"total_mb":%s,"free_mb":%s,"used_pct":%s},"memory":{"total_mb":%s,"free_mb":%s,"used_pct":%s},"load":{"1m":%s,"5m":%s,"15m":%s},"uptime_seconds":%s,"zram":{"used_mb":%s,"total_mb":%s}}\n' \
    "$HOSTNAME" "$HOSTNAME" \
    "$DISK_TOTAL" "$DISK_FREE" "$DISK_PCT" \
    "$MEM_TOTAL" "$MEM_FREE" "$MEM_PCT" \
    "$LOAD_1M" "$LOAD_5M" "$LOAD_15M" \
    "$UPTIME" "$ZRAM_USED" "$ZRAM_TOTAL"
