# ZFS Pre-Flight Checklist

**Machine:** qfox-1 (100.88.57.96)  
**Target kernel:** 7.0.9-1-cachyos (currently running 7.0.8-1-cachyos — one patch behind)  
**Pool name:** `stackcache`  
**Vdev:** sparse file at `/var/lib/stackcache/pool.img` (500 G) on `/dev/nvme0n1p2` (btrfs)  
**Script:** `4-Infrastructure/storage/zfs-pool-setup.sh`  
**Status:** ZFS module NOT loaded; reboot required first.

---

## 1. Block Device Inventory

```
NAME         SIZE  TYPE  MOUNTPOINT  FSTYPE
zram0        30.4G disk  [SWAP]      swap
nvme0n1       1.8T disk
├─nvme0n1p1    4G  part  /boot       vfat
└─nvme0n1p2  1.8T  part  /           btrfs
```

**Available space on btrfs root (`/dev/nvme0n1p2`):**

```
Size: 1.9 TB   Used: 174 GB   Avail: 1.7 TB   Use%: 10%
```

**There is only one NVMe. No raw partitions or spare disks are available.**  
The correct approach is a ZFS sparse-file vdev carved from the existing btrfs filesystem — exactly what `zfs-pool-setup.sh` does.  Btrfs + ZFS file vdevs coexist safely; ZFS handles its own checksumming and compression independently of btrfs `zstd:1`.

---

## 2. ZFS Module Status

```
modinfo zfs → ERROR: Module zfs not found.
zpool list  → The ZFS modules cannot be auto-loaded.
```

**Action required:** reboot into the 7.0.9-1-cachyos kernel once it is installed.  
Verify after reboot with:

```bash
uname -r                          # expect 7.0.9-1-cachyos
lsmod | grep "^zfs"               # must print a zfs line
modinfo zfs | head -3             # shows version
```

---

## 3. Exact Commands to Run After Reboot

Run these **in order** as root after confirming `lsmod | grep "^zfs"` is non-empty.

```bash
# 1. Confirm kernel and module
uname -r                          # 7.0.9-1-cachyos
lsmod | grep "^zfs"

# 2. Confirm free space (need ≥ 500 G available on btrfs)
df -h /var/lib                    # ≥ 500 G avail

# 3. Run the setup script (idempotent — safe to run again if pool exists)
sudo bash 4-Infrastructure/storage/zfs-pool-setup.sh

# 4. Verify pool came up
zpool status stackcache
zfs list -r stackcache

# 5. Confirm systemd services are enabled
systemctl is-enabled zfs-import-cache.service zfs-import-scan.service \
    zfs-mount.service zfs.target

# 6. Smoke-test thermal zone mounts
ls /mnt/stackcache/hot/db
ls /mnt/stackcache/warm/pgdump
ls /mnt/stackcache/warm/rclone
ls /mnt/stackcache/cold/snap

# 7. Confirm quotas
zfs get quota stackcache/hot/db
zfs get quota stackcache/warm/pgdump
zfs get quota stackcache/warm/rclone
zfs get quota stackcache/cold/snap
```

---

## 4. Pool Layout Recommendation

Single NVMe — no redundancy is possible with one disk. The sparse-file approach is the right call: it avoids repartitioning and gives ZFS its own namespace on top of btrfs.

```
stackcache          (500 G sparse file vdev, ashift=12, lz4 global)
├── hot/            (logbias=latency, primarycache=all, sync=standard)
│   └── hot/db      quota=150G, recordsize=16K   ← SQLite scratch
├── warm/           (logbias=throughput, primarycache=metadata, sync=disabled)
│   ├── warm/pgdump quota=150G, recordsize=128K, zstd-3  ← pg_dump / RDS
│   └── warm/rclone quota=50G,  recordsize=32K            ← rclone VFS cache
└── cold/           (logbias=throughput, primarycache=none, zstd-3, sync=disabled)
    └── cold/snap   quota=100G, recordsize=128K            ← ZFS send/recv
```

Total quotas: **450 G** on a 500 G pool → **50 G headroom** for pool metadata,
snapshot churn, and ZFS internal bookkeeping.

Boot re-import path: `zfs-import-cache.service` reads `/etc/zfs/zpool.cache`
(written by `zpool create -o cachefile=`). The scan-based fallback
(`zfs-import-scan.service`) is also enabled for resilience.

---

## 5. Issues Found in `zfs-pool-setup.sh` and Fixes Applied

All issues were fixed in-place. `bash -n` syntax check passes.

### Issue 1 — **No thermal-zone hierarchy** *(structural, fixed)*

**Before:** Pool had flat datasets `stackcache/db`, `stackcache/pgdump`,
`stackcache/rclone`, `stackcache/snap`.  
**After:** Datasets are nested under thermal-zone parents `hot/`, `warm/`, `cold/`
matching the UCM substrate schema:

```
stackcache/hot/db
stackcache/warm/pgdump
stackcache/warm/rclone
stackcache/cold/snap
```

Thermal-zone parents carry the tuning properties (`logbias`, `primarycache`,
`sync`) so child datasets inherit them, reducing per-dataset boilerplate and
making the routing intent explicit.

### Issue 2 — **Quota arithmetic left zero pool headroom** *(correctness, fixed)*

**Before:** `db=200G + pgdump=200G + rclone=50G + snap=50G = 500G` — exactly the
pool size. This left no free space for pool metadata, snapshot bookkeeping, or
ZFS internal structures, which would cause `ENOSPC` during normal operation.  
**After:** `hot/db=150G + warm/pgdump=150G + warm/rclone=50G + cold/snap=100G = 450G`,
leaving 50 G (10%) free.

### Issue 3 — **`cachefile` not set on pool creation** *(reliability, fixed)*

**Before:** `zpool create` had no `-o cachefile=` argument. File-vdev pools are
not automatically found by `zfs-import-scan` unless the vdev path is known at
scan time, which is fragile.  
**After:** `-o cachefile=/etc/zfs/zpool.cache` is passed to `zpool create`, and
`zfs-import-cache.service` is now enabled alongside `zfs-import-scan.service`.
The cache file is the canonical, reliable import path for file-vdev pools.

### Issue 4 — **`zfs-import-cache.service` not enabled** *(reliability, fixed)*

**Before:** Only `zfs-import-scan.service` was enabled.  
**After:** Both `zfs-import-cache.service` and `zfs-import-scan.service` are
enabled. Cache-based import runs first; scan is the fallback.

### Non-issues confirmed

- **Idempotency:** `zpool list "${POOL_NAME}" &>/dev/null` guard at top —
  already idempotent (prints status and exits 0 if pool exists). ✓
- **Device paths:** No hard-coded `/dev/sdX` paths — uses a sparse file under
  `/var/lib/stackcache/`. The btrfs root has 1.7 TB free, well above the 500 G
  vdev. ✓
- **`set -euo pipefail`:** Present. ✓
- **ZFS module check:** `lsmod | grep "^zfs"` guard present. ✓
- **`|| true` on `systemctl enable`:** Correct — prevents `set -e` abort if
  a service unit name differs slightly across kernel/distro versions. ✓

---

## 6. Thermal Routing Score → ZFS Dataset Placement

The `UniversalThermalRouter.compute_thermal_signature()` function in
`.devcontainer/Universal Computational Modeling.md` produces a score in [0, 1]:

```
score += 0.30  if urgency=True          (real-time required)
score += 0.02  per active_region        (spatial locality, up to 0.20)
score += 0.20  if char_time < 1e-3      (fast dynamics, fs/ps timescale)
score += 0.15  if scar_density > 0.5    (historically failure-prone → demote)
score += 0.15  if parallel_efficiency < 0.5  (poor scaling → batch)
```

| Score range | Zone | ZFS dataset path | Garage / restic role |
|---|---|---|---|
| `score < 0.2` | **hot** | `stackcache/hot/db` | — (local scratch only) |
| `0.2 ≤ score < 0.7` | **warm** | `stackcache/warm/pgdump` or `warm/rclone` | Garage S3 batch (`db-scratch`, `rds-overflow`) |
| `score ≥ 0.7` | **cold** | `stackcache/cold/snap` → then offload | restic snap → Garage `snap-zone` → gdrive cold copy |

### Concrete routing examples

| Workload | Score drivers | Score | Zone → Dataset |
|---|---|---|---|
| Active SQLite DB write | urgency=T, char_time<1ms | 0.50 | warm → `warm/pgdump` or `hot/db`\* |
| Interactive Lean proof search | urgency=T, active_regions>5 | 0.40–0.60 | warm → `warm/rclone` (VFS) |
| pg_dump / RDS COPY TO | urgency=F, large sequential | 0.15–0.30 | warm → `warm/pgdump` |
| ZFS send/recv from node | urgency=F, rare, archival | 0.70+ | cold → `cold/snap` |
| restic snapshot chunks | urgency=F, background | 0.70+ | cold → Garage `research-stack` |

\*SQLite scratch sits at the hot/warm boundary. Route to `hot/db` when
 `urgency=True AND char_time < 1ms`; otherwise `warm/pgdump` is acceptable.

---

## 7. Recommended `storage_agent.py` Changes for ZFS Thermal Zones

These are **recommendations only** — not applied here, as `storage_agent.py`
already passes `py_compile` and is in active use.

### 7.1 Add ZFS observation probe

`storage_agent.py` currently observes Garage and restic but has no ZFS
awareness. After the pool is live, add a `_probe_zfs(obs)` method that calls
`zpool list -H -o name,health,allocated,free stackcache` and adds:

```python
obs.zfs_pool_health: str        # "ONLINE" / "DEGRADED" / absent
obs.zfs_hot_used_pct_q16: int   # Q16_16 fraction of hot/db quota used
obs.zfs_warm_used_pct_q16: int
obs.zfs_cold_used_pct_q16: int
```

### 7.2 Add ZFS routing in the `decide()` function

When a ZFS zone exceeds ~80% of quota (`0xCCCC` in Q16_16 ≈ 0.8), trigger
the appropriate offload:

```python
# trigger_zfs_hot_evict: when hot/db > 80% quota
#   → mv stackcache/hot/db/... → warm, or flush to Garage db-scratch
# trigger_zfs_cold_offload: when cold/snap > 80% quota
#   → db-consolidate.sh offload to Garage snap-zone
```

### 7.3 Route `storage_agent.py` offloads through thermal paths

Currently `trigger_offload` always calls `db-consolidate.sh offload` which
pushes to Garage `db-scratch`. After ZFS is live, the agent could:

1. Write hot SQLite scratchwork to `stackcache/hot/db`
2. On `trigger_offload`, first snapshot: `zfs snapshot stackcache/warm/pgdump@agent-<ts>`
3. Then send to Garage `snap-zone` via `zfs send | aws s3 cp` rather than plain rclone.

This keeps the thermal routing provenance in the ZFS snapshot lineage.

### 7.4 Add `snap-zone` bucket observation

`obs.garage_buckets` already lists buckets. Add a check that `snap-zone` exists
once ZFS is live (it is already defined in AGENTS.md), and alert if missing:

```python
if "snap-zone" not in obs.garage_buckets:
    d.alerts.append("WARN: Garage snap-zone bucket missing — ZFS send/recv will fail")
```

---

## 8. Location Note

`AGENTS.md` (Infrastructure) lists `zfs-pool-setup.sh` under
`4-Infrastructure/storage/garage/` in the Garage scripts table. The file
actually lives at `4-Infrastructure/storage/zfs-pool-setup.sh` (one level up).
This is a documentation inconsistency — the file location is correct; the table
entry in AGENTS.md should be updated to point to `storage/zfs-pool-setup.sh`.
