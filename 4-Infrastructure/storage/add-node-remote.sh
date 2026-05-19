#!/usr/bin/env bash
# add-node-remote.sh
#
# Profiles a Tailscale node's available drives and adds it as:
#   1. An rclone SFTP remote  (node_<hostname>)
#   2. A ZFS replication target (zfs-send → rclone sftp)
#
# Known nodes (from tailscale status):
#   cupfox-4gb-2cpu   100.126.242.5
#   nixos             100.119.165.120
#   microvm-racknerd  100.101.247.127
#
# Usage:
#   bash add-node-remote.sh <tailscale-ip> [ssh-user] [ssh-port]
#
# Prerequisites on the target node (one-time):
#   1. Add this machine's ~/.ssh/id_ed25519.pub to the node's authorized_keys
#   2. Ensure rclone is installed on the node (for zfs-send receive)
#   3. For ZFS receive: zfs-utils installed on node
#
# After this script runs, the node appears as a Tier 1 cache target.
set -euo pipefail

NODE_IP="${1:?Usage: $0 <tailscale-ip> [user] [port]}"
SSH_USER="${2:-allaun}"
SSH_PORT="${3:-22}"
SSH_KEY="${HOME}/.ssh/id_ed25519"

SSH_OPTS="-i ${SSH_KEY} -p ${SSH_PORT} -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

# ── 1. Probe the node ──────────────────────────────────────────────────────────
echo "[add-node] Probing ${SSH_USER}@${NODE_IP}:${SSH_PORT}..."
PROFILE=$(ssh ${SSH_OPTS} "${SSH_USER}@${NODE_IP}" bash -s << 'REMOTE'
echo "hostname=$(hostname)"
echo "os=$(uname -s)"
echo "kernel=$(uname -r)"
# Total + free disk on / and any /data /mnt /storage paths
df -h --output=target,size,avail,use% 2>/dev/null | grep -v tmpfs | grep -v "^Filesystem" | while read mp sz av pct; do
    echo "mount=${mp} size=${sz} avail=${av} pct=${pct}"
done
# ZFS available?
which zfs 2>/dev/null && echo "zfs=yes" || echo "zfs=no"
# rclone available?
which rclone 2>/dev/null && echo "rclone=yes" || echo "rclone=no"
REMOTE
)

echo "[add-node] Profile:"
echo "$PROFILE"
echo ""

HOSTNAME=$(echo "$PROFILE" | grep "^hostname=" | cut -d= -f2)
REMOTE_NAME="node_${HOSTNAME//[-.]/_}"

# Pick the mount point with most free space
BEST_MOUNT=$(echo "$PROFILE" | grep "^mount=" | \
    awk -F'[ =]' '{for(i=1;i<=NF;i++) if($i=="avail") print $(i+1), $2}' | \
    sort -h | tail -1 | awk '{print $2}' | sed 's/mount=//')
[ -z "$BEST_MOUNT" ] && BEST_MOUNT="/"

echo "[add-node] Best mount on ${HOSTNAME}: ${BEST_MOUNT}"

# ── 2. Add rclone SFTP remote ─────────────────────────────────────────────────
echo "[add-node] Adding rclone remote '${REMOTE_NAME}'"
rclone config create "${REMOTE_NAME}" sftp \
    host "${NODE_IP}" \
    user "${SSH_USER}" \
    port "${SSH_PORT}" \
    key_file "${SSH_KEY}" \
    path_override "${BEST_MOUNT}/stackcache" \
    shell_type unix \
    md5sum_command "md5sum" \
    sha1sum_command "sha1sum"

# ── 3. Create cache directory on node ─────────────────────────────────────────
echo "[add-node] Creating /stackcache directory on ${HOSTNAME}"
ssh ${SSH_OPTS} "${SSH_USER}@${NODE_IP}" \
    "sudo mkdir -p ${BEST_MOUNT}/stackcache/db ${BEST_MOUNT}/stackcache/pgdump ${BEST_MOUNT}/stackcache/snap && sudo chown -R ${SSH_USER}: ${BEST_MOUNT}/stackcache"

# ── 4. Smoke-test rclone remote ───────────────────────────────────────────────
echo "[add-node] Testing rclone remote..."
rclone lsd "${REMOTE_NAME}:" 2>&1 | head -5

# ── 5. Register node in the node registry ─────────────────────────────────────
REGISTRY_FILE="$(dirname "$0")/node-registry.json"
python3 - << PYEOF
import json, os, sys
from datetime import datetime, timezone

registry_path = "${REGISTRY_FILE}"
entry = {
    "hostname": "${HOSTNAME}",
    "tailscale_ip": "${NODE_IP}",
    "ssh_user": "${SSH_USER}",
    "ssh_port": ${SSH_PORT},
    "rclone_remote": "${REMOTE_NAME}",
    "cache_path": "${BEST_MOUNT}/stackcache",
    "zfs_available": $( echo "$PROFILE" | grep -c "zfs=yes" || true ),
    "added_at": datetime.now(timezone.utc).isoformat()
}

registry = []
if os.path.exists(registry_path):
    with open(registry_path) as f:
        registry = json.load(f)

# Replace if hostname already exists
registry = [r for r in registry if r.get("hostname") != entry["hostname"]]
registry.append(entry)
with open(registry_path, "w") as f:
    json.dump(registry, f, indent=2)
print(f"[add-node] Registered {entry['hostname']} -> {entry['rclone_remote']}")
PYEOF

echo ""
echo "[add-node] Done. '${REMOTE_NAME}' is now Tier 1 cache for stackcache."
echo "  Run:  rclone ls ${REMOTE_NAME}:db/"
echo "  ZFS send target:  ${REMOTE_NAME}:snap/"
