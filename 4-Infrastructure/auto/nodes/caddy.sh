#!/bin/bash
# caddy.sh — Caddy status probe (runs on microvm-racknerd)
# Output: JSON with cert expiry, service status, disk.

caddy_running=false
if systemctl is-active --quiet caddy 2>/dev/null; then
    caddy_running=true
fi

# Check certificate expiry
cert_days=0
cert_expiry="unknown"
cert_info=$(openssl s_client -connect localhost:443 -servername researchstack.info </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ -n "$cert_info" ]; then
    not_after=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
    if [ -n "$not_after" ]; then
        not_after_epoch=$(date -d "$not_after" +%s 2>/dev/null || echo 0)
        if [ "$not_after_epoch" -gt 0 ]; then
            now_epoch=$(date +%s)
            cert_days=$(( (not_after_epoch - now_epoch) / 86400 ))
            cert_expiry=$(date -d "@$not_after_epoch" +%Y-%m-%d 2>/dev/null || echo "unknown")
        fi
    fi
fi

# Disk usage for static files
disk_info=$(df -k / 2>/dev/null | awk 'NR==2 {printf "%.0f %.0f %s", $2/1024, $4/1024, $5}')
DISK_TOTAL=$(echo "$disk_info" | awk '{print $1}')
DISK_FREE=$(echo "$disk_info" | awk '{print $2}')
DISK_PCT=$(echo "$disk_info" | awk '{print $3}' | tr -d '%')

printf '{"caddy_running":%s,"cert_days_remaining":%s,"cert_expiry":"%s","disk_total_mb":%s,"disk_free_mb":%s,"disk_used_pct":%s}\n' \
    "$caddy_running" "$cert_days" "$cert_expiry" "$DISK_TOTAL" "$DISK_FREE" "$DISK_PCT"
