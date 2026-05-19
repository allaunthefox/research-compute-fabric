#!/usr/bin/env bash
# zfs-pool-setup.sh
#
# Creates a ZFS pool named "stackcache" backed by a sparse file on the local
# NVMe btrfs filesystem.  This is Tier 0 of the three-tier cache:
#
#   Tier 0  stackcache  (local NVMe, ZFS, fast scratch)          ← this script
#   Tier 1  node drives (rclone SFTP, see add-node-remote.sh)
#   Tier 2  gdrive:research-stack-offload  (cold overflow)
#
# Why a sparse file instead of a raw partition?
#   The NVMe is already partitioned (btrfs root).  A sparse file lets us
#   carve out ZFS space without repartitioning.  Btrfs + ZFS file vdevs
#   coexist safely; ZFS does its own checksumming and compression.
#
# Pool layout:
#   /var/lib/stackcache/pool.img   — 500 GB sparse vdev file
#   mounted at /mnt/stackcache
#
# Thermal-zone dataset hierarchy (per Universal Computational Modeling substrate):
#   stackcache/hot                 — ZIL-backed, sub-second latency, high urgency
#     stackcache/hot/db            — active SQLite scratch databases
#   stackcache/warm                — batch I/O, moderate latency
#     stackcache/warm/pgdump       — pg_dump / COPY TO overflow from Aurora RDS
#     stackcache/warm/rclone       — rclone VFS cache directory
#   stackcache/cold                — archival, high compression, sequential I/O
#     stackcache/cold/snap         — ZFS send/receive landing zone for node data
#
# Routing score (from UniversalThermalRouter.compute_thermal_signature):
#   score < 0.2  → hot   (urgency, fast dynamics, real-time feedback)
#   score < 0.7  → warm  (batch, conformational sampling, ensemble)
#   score ≥ 0.7  → cold  (rare events, long-term, archival)
#
# Quotas leave ≥10% pool headroom for metadata and snapshots:
#   hot/db:      150 G
#   warm/pgdump: 150 G
#   warm/rclone:  50 G
#   cold/snap:   100 G
#   Total quotas: 450 G  (pool is 500 G → 50 G free for metadata/snapshots)
#
# Requires: ZFS kernel module loaded (reboot after installing cachyos-zfs)
# Run as: sudo bash zfs-pool-setup.sh
set -euo pipefail

POOL_NAME="stackcache"
VDEV_DIR="/var/lib/stackcache"
VDEV_FILE="${VDEV_DIR}/pool.img"
VDEV_SIZE="500G"
MOUNT_BASE="/mnt/stackcache"
ZFS_CACHE_FILE="/etc/zfs/zpool.cache"

# ── Preflight ──────────────────────────────────────────────────────────────────
if ! lsmod | grep -q "^zfs"; then
    echo "ERROR: ZFS module not loaded. Reboot into the 7.0.9-1-cachyos kernel first." >&2
    exit 1
fi

if zpool list "${POOL_NAME}" &>/dev/null; then
    echo "Pool '${POOL_NAME}' already exists — nothing to do."
    zpool status "${POOL_NAME}"
    zfs list -r "${POOL_NAME}"
    exit 0
fi

# ── Create sparse vdev file ────────────────────────────────────────────────────
echo "[zfs-setup] Creating ${VDEV_SIZE} sparse vdev at ${VDEV_FILE}"
mkdir -p "${VDEV_DIR}"
# truncate creates a sparse file — uses no actual disk blocks until written
truncate -s "${VDEV_SIZE}" "${VDEV_FILE}"
chmod 600 "${VDEV_FILE}"

# ── Create pool ────────────────────────────────────────────────────────────────
# -o cachefile: ensures zpool.cache is written so zfs-import-cache.service
#   can reliably reimport the file-vdev pool on next boot without a full scan.
echo "[zfs-setup] Creating zpool '${POOL_NAME}'"
zpool create \
    -o ashift=12 \
    -o cachefile="${ZFS_CACHE_FILE}" \
    -O compression=lz4 \
    -O atime=off \
    -O xattr=sa \
    -O mountpoint="${MOUNT_BASE}" \
    "${POOL_NAME}" "${VDEV_FILE}"

# ── Create thermal-zone parent datasets ───────────────────────────────────────
echo "[zfs-setup] Creating thermal-zone parent datasets (hot / warm / cold)"

# HOT zone: ZIL-backed, low latency, primarycache=all for ARC warmth
# logbias=latency tells ZFS to prefer ZIL for synchronous writes
zfs create \
    -o logbias=latency \
    -o primarycache=all \
    -o sync=standard \
    "${POOL_NAME}/hot"

# WARM zone: batch throughput, metadata-only ARC
zfs create \
    -o logbias=throughput \
    -o primarycache=metadata \
    -o sync=disabled \
    "${POOL_NAME}/warm"

# COLD zone: archival, heavy compression, no ARC pressure
zfs create \
    -o logbias=throughput \
    -o primarycache=none \
    -o compression=zstd-3 \
    -o sync=disabled \
    "${POOL_NAME}/cold"

# ── Create workload datasets under thermal zones ───────────────────────────────
echo "[zfs-setup] Creating workload datasets"

# HOT: SQLite scratch — fast random I/O, 16 K recordsize for small random writes
zfs create \
    -o recordsize=16K \
    "${POOL_NAME}/hot/db"

# WARM: pg_dump / COPY TO overflow — large sequential writes
zfs create \
    -o recordsize=128K \
    -o compression=zstd-3 \
    "${POOL_NAME}/warm/pgdump"

# WARM: rclone VFS cache — matches rclone's default chunk sizes
zfs create \
    -o recordsize=32K \
    "${POOL_NAME}/warm/rclone"

# COLD: ZFS send/receive landing zone for node data consolidation
# (Garage bucket: snap-zone)
zfs create \
    -o recordsize=128K \
    "${POOL_NAME}/cold/snap"

# ── Quotas ────────────────────────────────────────────────────────────────────
# Total: 450 G quotas on a 500 G pool → ~50 G headroom for metadata + snapshots.
# (Previous layout summed to exactly 500 G, leaving zero headroom.)
zfs set quota=150G "${POOL_NAME}/hot/db"
zfs set quota=150G "${POOL_NAME}/warm/pgdump"
zfs set quota=50G  "${POOL_NAME}/warm/rclone"
zfs set quota=100G "${POOL_NAME}/cold/snap"

# ── Auto-import on boot ────────────────────────────────────────────────────────
# Enable both cache-based and scan-based import services.
# zfs-import-cache.service is the preferred path when cachefile is set;
# zfs-import-scan.service is the fallback.
echo "[zfs-setup] Enabling ZFS systemd services"
systemctl enable --now \
    zfs-import-cache.service \
    zfs-import-scan.service \
    zfs-mount.service \
    zfs.target 2>/dev/null || true

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "[zfs-setup] Done."
zpool status "${POOL_NAME}"
echo ""
zfs list -r "${POOL_NAME}"
echo ""
echo "Thermal zone mounts:"
echo "  HOT  — SQLite scratch:  ${MOUNT_BASE}/hot/db"
echo "  WARM — RDS overflow:    ${MOUNT_BASE}/warm/pgdump"
echo "  WARM — rclone VFS:      ${MOUNT_BASE}/warm/rclone"
echo "  COLD — Node snap zone:  ${MOUNT_BASE}/cold/snap"
echo ""
echo "Routing: score<0.2 → hot | score<0.7 → warm | score≥0.7 → cold"
