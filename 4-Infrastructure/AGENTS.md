# AGENTS.md - Infrastructure And Hardware

Scope: `4-Infrastructure/`

## Rules

- Keep infrastructure scripts receipt-bearing: every probe should have a
  machine-readable output or update an existing receipt.
- Separate software witnesses from live hardware witnesses.
- Do not claim FPGA acceleration from bitstream generation alone.
- Do not claim UART/fabric success without observed bytes or a matching hardware
  receipt.
- Treat `/usr/bin/sem` as GNU Parallel on this machine unless proven otherwise;
  use the isolated `sem` binary documented in stack solidification receipts when
  needed.
- Remote model/API probes must be secret-clean. Read provider credentials from
  environment variables only (`OLLAMA_API_KEY`, `DEEPSEEK_API_KEY`, etc.); never
  embed literal keys in scripts, receipts, prompts, or docs.
- LLM/model outputs are reviewer receipts, not validation. If a model review is
  promoted, store the answer and a machine-readable receipt with prompt/answer
  hashes under `shared-data/artifacts/`, and state which files formed the
  context.

## Preferred Checks

```bash
python3 -m py_compile 4-Infrastructure/shim/<script>.py
python3 -m json.tool <receipt>.json >/dev/null
```

For API-facing or receipt-writing scripts, also run a touched-file secret scan
before staging. Treat the repository credential hook as a backstop, not the
first detector.

For Tang Nano 9K work, keep the boundaries explicit:

- bitstream present
- SRAM load
- flash persistence
- UART beacon
- Q16/software witness
- Q16/live hardware witness

## Storage Stack: restic + Garage + rclone

Three tools, three distinct jobs — no overlap:

| Tool | Job | Does NOT do |
|------|-----|------------|
| **restic** | Deduplicated, encrypted, content-addressed snapshots. Point-in-time restore. Verifiable integrity. | Raw sync, remotes management |
| **Garage** | Self-hosted S3-compatible object store across Tailscale nodes. restic's primary backend. | Dedup, encryption, scheduling |
| **rclone** | Moves raw objects between remotes (Garage↔gdrive, gdrive↔Garage). Cold-copy of restic chunks to gdrive. | Dedup, encryption, snapshots |

### Data flow

```
git commit
    └─(post-commit hook, async)─▶ restic snap ──────────────────▶ Garage:research-stack
                                   restic snap-db (SQLite)         (deduplicated, encrypted)
                                   restic snap-rds (pg_dump|zstd)  │
                                                                    │
Daily 03:00 (systemd timer)                                        │
    ├─ rclone copy ─────────────────────────────────────────────── ▶ gdrive:restic-mirror/
    │  (cold copy of restic chunks — survive Garage loss)
    └─ rclone sync ─── gdrive:research-stack ──▶ Garage:gdrive-mirror
                        (S3-native access to gdrive data)

Restore path A (Garage up):
    restic restore <id> -r s3:http://localhost:3900/research-stack

Restore path B (Garage down, gdrive available):
    restic restore <id> -r rclone:gdrive:restic-mirror
```

### Garage S3 — node topology (Tailscale mesh)

All object storage for this stack uses **Garage v2.3.0** — a single-binary,
Dynamo-style S3-compatible store written in Rust. Replaced rclone serve s3.

### Node topology (Tailscale mesh)

| Node | Tailscale IP | Role | Disk |
|------|-------------|------|------|
| qfox-1 (this machine) | 100.88.57.96 | primary, S3 endpoint | 1.8 TB NVMe |
| cupfox-4gb-2cpu | 100.126.242.5 | storage node | TBD |
| nixos | 100.119.165.120 | storage node | TBD |
| microvm-racknerd | 100.101.247.127 | storage node (VPS) | TBD |

- RPC port: **3901** (Tailscale-only, not exposed to internet)
- S3 API port: **3900** (qfox-1 only; other nodes bind loopback)
- Admin API port: **3903** (loopback only on all nodes)

### Garage S3 buckets

| Bucket | Purpose |
|--------|---------|
| `research-stack` | Primary project objects |
| `db-scratch` | Active SQLite scratch databases |
| `rds-overflow` | pg_dump / COPY TO exports from Aurora RDS |
| `snap-zone` | ZFS send/receive snapshots |
| `gdrive-mirror` | Mirror of gdrive:research-stack |

### Credentials

Credentials live in `/etc/garage/garage.env` (mode 600, never committed).
Sourced automatically by all storage scripts. Inside devcontainer, set:
```bash
source /etc/garage/garage.env
export AWS_ACCESS_KEY_ID=$GARAGE_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$GARAGE_SECRET_ACCESS_KEY
export AWS_ENDPOINT_URL=http://host.containers.internal:3900
export AWS_DEFAULT_REGION=garage
```

### Restic scripts (`4-Infrastructure/storage/restic/`)

| Script | Purpose |
|--------|---------|
| `restic.env` | Source this to load all credentials + repo paths |
| `backup.sh snap [tag]` | Snapshot repo tree → Garage |
| `backup.sh snap-db [dir]` | Snapshot SQLite scratch DBs → Garage |
| `backup.sh snap-rds <table>` | Stream pg_dump \| zstd → restic stdin → Garage |
| `backup.sh cold-copy` | rclone copy Garage:research-stack → gdrive:restic-mirror |
| `backup.sh sync-gdrive` | rclone sync gdrive:research-stack → Garage:gdrive-mirror |
| `backup.sh forget` | Apply retention (7 daily / 4 weekly / 6 monthly) + prune |
| `backup.sh verify` | restic check --read-data-subset=5% |
| `backup.sh snapshots` | List all snapshots |
| `backup.sh restore <id> <dst>` | Restore a snapshot |
| `backup.sh full` | snap + cold-copy + sync-gdrive + forget |

Restic repo: `s3:http://localhost:3900/research-stack` (Garage primary)
Cold copy:   `rclone:gdrive:restic-mirror` (survives Garage loss)
Password:    `/etc/garage/restic-password` (chmod 644, not committed)

Daily timer: `restic-backup.timer` fires at 03:00 ±30 min, runs `backup.sh full`.

### Garage scripts (`4-Infrastructure/storage/garage/`)

| Script | Purpose |
|--------|---------|
| `zfs-pool-setup.sh` | Create ZFS pool on local NVMe (run after reboot into 7.0.9 kernel) |
| `garage-node-bootstrap.sh <ip>` | Install Garage on a new node, register in node-registry.json |
| `garage-cluster-init.sh` | Connect nodes, assign zones, bump replication_factor to 3 |
| `db-consolidate.sh` | Direct Garage offload/consolidate (used by backup.sh internally) |

All scripts live in `4-Infrastructure/storage/garage/`:

| Script | Purpose |
|--------|---------|
| `zfs-pool-setup.sh` | Create ZFS pool on local NVMe (run after reboot into 7.0.9 kernel) |
| `garage-node-bootstrap.sh <ip>` | Install Garage on a new node, register in node-registry.json |
| `garage-cluster-init.sh` | Connect nodes, assign layout, bump replication_factor to 3 |
| `db-consolidate.sh offload [dir]` | Push SQLite DBs → s3://db-scratch/ |
| `db-consolidate.sh rds-dump <table>` | Dump RDS table → s3://rds-overflow/ |
| `db-consolidate.sh consolidate` | Restore static s3://rds-overflow/ objects → RDS |
| `db-consolidate.sh sync-gdrive` | Mirror gdrive:research-stack → s3://gdrive-mirror/ |
| `db-consolidate.sh status` | Show cluster and bucket state |

### Replication status

Currently `replication_factor = 1` (single node, qfox-1 only).
Bump to 3 after bootstrapping 3 nodes:
```bash
bash 4-Infrastructure/storage/garage/garage-node-bootstrap.sh 100.126.242.5
bash 4-Infrastructure/storage/garage/garage-node-bootstrap.sh 100.119.165.120
bash 4-Infrastructure/storage/garage/garage-cluster-init.sh
```

### Git post-commit hook

`.git/hooks/post-commit` automatically runs `db-consolidate.sh offload` +
`db-consolidate.sh consolidate` in the background after every commit.
Non-blocking. Skipped silently if Garage isn't running.
Log at `~/.cache/garage-post-commit.log`.

### gdrive integration

gdrive is still mounted via rclone at `/home/allaun/gdrive` for direct file
access. The `db-consolidate.sh sync-gdrive` command mirrors it into the
`gdrive-mirror` Garage bucket for S3-native access without hitting Drive API
quotas on every read.

Drive API safe-use rules still apply to any direct rclone → gdrive operations:
- `--drive-pacer-min-sleep 200ms` — ≤5 TPS sustained
- `--drive-pacer-burst 10` — limits burst before pacer beats
- `--dir-cache-time 10m` — warm cache = zero API calls

## Storage Agent (`4-Infrastructure/storage/storage_agent.py`)

Full-loop observer, optimizer, and actor for the restic + Garage + rclone stack.

### Design contract

**Shim boundary** (per AGENTS.md §7.1):

- ALLOWED: subprocess calls to existing CLI tools (`backup.sh`, `db-consolidate.sh`,
  `restic`, `aws s3`), JSON I/O, JSONL log, receipt assembly, threshold
  comparisons on Q16_16-encoded integers.
- FORBIDDEN: reimplementing restic/Garage/rclone logic, Float arithmetic, cost
  functions (those belong in Lean), new external dependencies.

### Observe → Decide → Act → Emit loop

```
Observation          Decision              ActionResult
─────────────────    ──────────────────    ──────────────────
garage_up            trigger_snap          actions_attempted
garage_buckets       trigger_cold_copy     actions_succeeded
restic_snapshot_count trigger_verify       actions_failed
dedup_ratio_q16      trigger_forget        details
backup_log_last_ok   trigger_offload
cold_copy_needed     trigger_garage_restart
errors               alerts / rationale
```

All numeric thresholds are Q16_16 (UInt32, one = 0x00010000 = 65536).
No Float arithmetic. Threshold constants defined at the top of the file.

### Receipt schema: `storage_agent_receipt_v1`

Every cycle emits one receipt:

```json
{
  "schema":           "storage_agent_receipt_v1",
  "version":          "1.0.0",
  "generated_at_utc": "<ISO-8601>",
  "tick":             <int>,
  "parent_hash":      "<sha256 of previous receipt>",
  "observation":      { ... },
  "decision":         { ... },
  "action_result":    { ... },
  "claim_boundary":   "storage-agent-observe-decide-act-only",
  "receipt_hash":     "<sha256 of canonical preimage>"
}
```

Two sinks:
1. **Local JSONL hash-chain**: `~/.cache/storage-agent.jsonl` — fast local access,
   survives Garage loss.
2. **Garage S3**: `s3://research-stack/agent-receipts/<date>/<hash16>.json` —
   durable, indexed by date.

### Trigger model

| Trigger | Condition | Action |
|---------|-----------|--------|
| `trigger_snap` | No snapshots, or backup log shows no recent success | `backup.sh snap agent-triggered` |
| `trigger_cold_copy` | Newest snapshot > 26 h old (daily timer may have missed) | `backup.sh cold-copy` |
| `trigger_verify` | dedup_ratio_q16 < 0.3 AND snapshot_count > 5 | `backup.sh verify` |
| `trigger_forget` | snapshot_count > 30 | `backup.sh forget` (prune) |
| `trigger_offload` | Garage is up (idempotent) | `db-consolidate.sh offload` |
| `trigger_garage_restart` | Garage unreachable | `systemctl restart garage.service` |

### Systemd units

| File | Purpose |
|------|---------|
| `storage-agent.service` | One-shot service (Type=oneshot, User=allaun) |
| `storage-agent.timer`   | Fires every 15 min (OnCalendar=*:0/15, RandomizedDelaySec=60) |

Installation:
```bash
sudo cp 4-Infrastructure/storage/storage-agent.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now storage-agent.timer
```

### Post-commit integration

`.git/hooks/post-commit` runs the agent (`--once`) in the background after
each `backup.sh snap` completes. The agent observes the post-snap state and
takes any follow-on corrective actions (offload, cold-copy if stale, etc.).
Log at `~/.cache/storage-agent.log`.

### Usage

```bash
# One-shot probe (observe only, no actions)
python3 4-Infrastructure/storage/storage_agent.py --probe-only

# One-shot, full loop
python3 4-Infrastructure/storage/storage_agent.py --once

# Show what would be done
python3 4-Infrastructure/storage/storage_agent.py --dry-run

# Skip S3 receipt upload (local JSONL only)
python3 4-Infrastructure/storage/storage_agent.py --no-s3

# Daemon mode (rarely needed; systemd timer is preferred)
python3 4-Infrastructure/storage/storage_agent.py --loop --interval 900
```

### Log paths

| Path | Contents |
|------|---------|
| `~/.cache/storage-agent.jsonl` | Hash-chained JSONL receipt log |
| `~/.cache/storage-agent.log` | Human-readable stdout/stderr from systemd and hook runs |
| `s3://research-stack/agent-receipts/` | Durable S3 receipts (Garage) |

## Current Stack-Solidification Anchors

- `4-Infrastructure/shim/stack_solidification_audit.py`
- `4-Infrastructure/shim/stack_fail_closure_register.py`
- `4-Infrastructure/shim/beaver_mask_freshness_negative_controls.py`
- `4-Infrastructure/shim/tang9k_uart_beacon_probe.py`
- `4-Infrastructure/shim/hutter_jxl_starfield_eigenprobe.py`
- `4-Infrastructure/shim/hutter_jxl_starfield_replay_verify.py`
