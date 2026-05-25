# Infrastructure Status — Research Stack

> **Last verified:** 2026-05-23
> **Scope:** All live nodes, services, and storage in the Tailscale mesh.

---

## Tailscale Mesh

All nodes route through Tailscale. No public ports are open on any node except `microvm-racknerd` (ports 80/443 for Caddy).

| Node | Tailscale IP | Hostname | Role | OS | SSH |
|------|-------------|----------|------|-----|-----|
| **qfox-1** | 100.88.57.96 | QFox | Garage primary, S3 endpoint, GPU compute, build host | Arch Linux 7.0.9-cachyos | local |
| **nixos-laptop** | 100.102.173.61 | nixos | Authentik SSO, k3s control plane, storage node | NixOS 26.05 (Yarara) | key OK |
| **361395-1** | 100.110.163.82 | 361395 | Netcup VPS, Garage storage node | Debian 13 | key OK |
| **microvm-racknerd** | 100.101.247.127 | MicroVM-Racknerd | Caddy reverse proxy, public edge | Debian (microVM) | root password OK |
| **nixos-steamdeck-1** | 100.85.244.73 | steamdeck | GPU compute, planned edge LLM (3B-7B) | NixOS | just onboarded |
| **dracocomp** | 100.100.140.27 | — | offline / unreachable | — | unreachable 3+ days |

---

## Public Edge: Caddy on microvm-racknerd

Caddy v2.11.3 with Porkbun DNS plugin handles all public HTTPS traffic.

### Wildcard TLS

- **Certificate:** `*.researchstack.info` + `researchstack.info`
- **Issuer:** Let's Encrypt E7
- **Challenge:** DNS-01 via Porkbun API
- **Valid:** 2026-05-21 → 2026-08-19
- **Renewal:** automatic

### Domains & Routing

| Domain | Caddy Action | Upstream (Tailscale) | Notes |
|--------|-------------|----------------------|-------|
| `researchstack.info` | `forward_auth` + `reverse_proxy` | `100.102.173.61:30803` | Homer dashboard (landing page) |
| `chat.researchstack.info` | `forward_auth` + `file_server` | `100.102.173.61:9000` (auth only) | Placeholder HTML |
| `dash.researchstack.info` | `forward_auth` + `reverse_proxy` | `100.102.173.61:30802` | Heimdall (k3s NodePort) |
| `status.researchstack.info` | `forward_auth` + `reverse_proxy` | `100.102.173.61:30801` | Uptime Kuma (k3s NodePort) |
| `auth.researchstack.info` | `reverse_proxy` (direct) | `100.102.173.61:9000` | Authentik SSO (no forward_auth loop) |

### Caddy Service

- **Config:** `/etc/caddy/Caddyfile`
- **Service:** `caddy.service` (systemd)
- **Status:** active
- **Env:** Porkbun credentials via systemd drop-in (`/etc/systemd/system/caddy.service.d/override.conf`)
- **Disk:** 9.1G total, 6.4G free

---

## Identity: Authentik on nixos-laptop

Authentik runs as standalone Podman containers (not k3s). The k3s Helm migration is pending.

### Containers

| Container | Image | Port | Status |
|-----------|-------|------|--------|
| `authentik_postgresql_1` | `postgres:16-alpine` | 5432/tcp | Up, healthy |
| `authentik_valkey_1` | `valkey/valkey:8-alpine` | 6379/tcp | Up, healthy |
| `authentik_server_1` | `ghcr.io/goauthentik/server:2026.2.3` | 0.0.0.0:9000→9000, 0.0.0.0:9443→9443 | Up |
| `authentik_worker_1` | `ghcr.io/goauthentik/server:2026.2.3` | — | Up |

### Compose

- **Path:** `/home/allaun/authentik/docker-compose.yml`
- **Network:** `authentik_authentik` (bridge)
- **Volumes:** `database`, `redis`, `media`, `custom-templates`, `certs`

### Valkey Migration

Redis was replaced with Valkey 8 (Alpine) on 2026-05-22. The `redis` volume was wiped during migration because Valkey does not read Redis RDB format version 13. Authentik cache/session data was lost but rebuilds automatically on first use.

---

## k3s on nixos-laptop

k3s v1.35.4+k3s1 runs as a single-node control plane. Authentik was **not** successfully migrated to k3s.

### Running Services (services namespace)

| Pod | Service | NodePort | Status |
|-----|---------|----------|--------|
| `uptime-kuma` | `uptime-kuma` | 30801 | Running |
| `heimdall` | `heimdall` | 30802 | Running |
| `homer` | `homer` | 30803 | Running |
| `pulse-receiver` | `pulse-receiver` | 30804 | Running |

### Blocked / Broken

| Pod | Status | Blocker |
|-----|--------|---------|
| `authentik-postgresql-0` | CrashLoopBackOff | Bitnami PostgreSQL subchart: read-only filesystem on `/var/run/postgresql` |
| `authentik-redis-master-0` | ImagePullBackOff | Bitnami Redis image tags no longer exist |
| `authentik-server-*` | Running (0/1) | Waiting for PostgreSQL |
| `authentik-worker-*` | CrashLoopBackOff | Waiting for PostgreSQL |
| `helm-install-authentik-*` | Error | Helm revision failures cascade |

**Decision:** Keep Authentik on standalone Podman. Decommission or fix the k3s Authentik HelmChart when time permits.

---

## Storage: Garage S3

Garage v2.3.0 provides a self-hosted, replicated S3-compatible object store.

### Cluster Topology

| Node ID | Hostname | Address | Zone | Capacity | Usable | DataAvail |
|---------|----------|---------|------|----------|--------|-----------|
| `3e08a71b73fa2b10` | QFox | 100.88.57.96:3901 | local | 780.4 GiB | 68.9 GiB | 1.5 TiB (83.5%) |
| `75fac43bc53eb201` | 361395 | 100.110.163.82:3901 | fra | 68.9 GiB | 68.9 GiB | 65.2 GiB (52.3%) |
| `a7e6c283056a4d77` | nixos | 100.102.173.61:3901 | ord | 346.5 GiB | 68.9 GiB | 393.5 GiB (85.8%) |

- **Replication factor:** 3
- **Zone redundancy:** maximum
- **Effective capacity:** 68.9 GiB (bottlenecked by 361395-1)
- **Layout version:** 1

### Ports

| Port | Purpose | Binding |
|------|---------|---------|
| 3900 | S3 API | qfox-1 only (localhost + Tailscale) |
| 3901 | RPC (inter-node) | all nodes, Tailscale |
| 3903 | Admin API | loopback only |

### Buckets

| Alias | Purpose |
|-------|---------|
| `research-stack` | Primary project objects |
| `db-scratch` | Active SQLite scratch databases |
| `rds-overflow` | pg_dump / COPY TO exports |
| `snap-zone` | ZFS send/receive snapshots |
| `gdrive-mirror` | Mirror of gdrive:research-stack |

### Nodes

**qfox-1**
- Garage runs as systemd service (`garage.service`) under dedicated `garage` user
- S3 API bound to localhost:3900 (forwarded via SSH tunnel for remote access)
- NixOS-style persistence not needed (native Arch)

**361395-1**
- Garage runs as systemd service
- zram enabled: 2G zstd swap
- Disk: 125G total, 66G free

**nixos-laptop**
- Garage runs as systemd service via NixOS module
- zram enabled in `/etc/nixos/configuration.nix`
- Disk: 459G NVMe, 394G free
- Binary path: not in default `$PATH`; managed by NixOS

---

## Backups: restic + rclone

### Primary restic repo

- **Backend:** `s3:http://localhost:3900/research-stack` (Garage)
- **Password file:** `/etc/garage/restic-password`

### Scripts

All scripts live in `4-Infrastructure/storage/restic/`:

| Script | Purpose |
|--------|---------|
| `backup.sh snap [tag]` | Snapshot repo tree → Garage |
| `backup.sh snap-db [dir]` | Snapshot SQLite scratch DBs |
| `backup.sh snap-rds <table>` | Stream pg_dump \| zstd → restic stdin |
| `backup.sh cold-copy` | rclone copy Garage → gdrive:restic-mirror |
| `backup.sh sync-gdrive` | rclone sync gdrive:research-stack → Garage:gdrive-mirror |
| `backup.sh forget` | Retention prune (7d/4w/6m) |
| `backup.sh verify` | restic check --read-data-subset=5% |
| `backup.sh full` | snap + cold-copy + sync-gdrive + forget |

### Schedule

- **Daily timer:** `restic-backup.timer` fires at 03:00 ±30 min
- **Post-commit hook:** `.git/hooks/post-commit` runs `db-consolidate.sh offload` + `consolidate` in background

---

## Secrets

SOPS/age is used for all secrets.

- **Age key:** `~/.config/sops/age/keys.txt`
- **Public key:** `age1tp4vr565zkmvnyulatpyaj6z8zrz7q9mpaypz85yz8rty99crdasualxyr`
- **Config:** `.sops.yaml` (repo root) + `4-Infrastructure/k3s-flake/.sops.yaml`

### Encrypted files (selection)

| File | Contents |
|------|----------|
| `4-Infrastructure/infra/secrets/credentials.json` | Provider API keys |
| `4-Infrastructure/infra/secrets/appflowy.env` | AppFlowy secrets |
| `4-Infrastructure/deploy/cupfox/pre-infect-backup/porkbun.env` | Porkbun API key + secret |
| `4-Infrastructure/storage/restic/restic.env` | Restic + Garage credentials |
| `API KEYS/racknerd_510bd9c_root.txt` | Racknerd credentials |

### Porkbun DNS

- API key + secret stored in SOPS-encrypted `porkbun.env`
- Used by Caddy for DNS-01 wildcard certificate challenges
- Verified working: `/ping` and `/dns/retrieve/researchstack.info`

---

## Post-Quantum Cryptography

| Layer | Status |
|-------|--------|
| **Tailscale** | X25519Kyber768 hybrid key exchange active (v1.98+) |
| **SSH (all nodes)** | `mlkem768x25519-sha256` preferred in `sshd_config` and `ssh_config` |
| **Garage RPC** | Tailscale transport only (no direct PQ on RPC layer) |

---

## Node Details

### qfox-1

| Spec | Value |
|------|-------|
| OS | Arch Linux, kernel 7.0.9-1-cachyos |
| CPU | AMD Ryzen (GPU compute available) |
| Disk | 1.8 TB NVMe |
| Memory | — |
| Tailscale | 100.88.57.96 |
| Garage | primary node, S3 endpoint |
| SSH config | `~/.ssh/config` entry `qfox-1` (local) |

### nixos-laptop

| Spec | Value |
|------|-------|
| OS | NixOS 26.05.20260521.f83fc3c (Yarara) |
| Disk | 459G NVMe, 394G free |
| Memory | 14 GiB total |
| Tailscale | 100.102.173.61 |
| k3s | v1.35.4+k3s1, single-node control plane |
| Authentik | Podman, port 9000 |
| Garage | storage node (ord zone) |
| zram | enabled in NixOS config |

### 361395-1 (Netcup VPS)

| Spec | Value |
|------|-------|
| OS | Debian 13 (OpenSSH_10.0p2) |
| Public IP | 46.232.249.226 |
| Disk | 125G, 66G free |
| Memory | — |
| Tailscale | 100.110.163.82 |
| Garage | storage node (fra zone) |
| zram | 2G zstd (manual `zramctl`) |
| APT issues | `enterprise.proxmox.com` returns 401; `pve-no-subscription` repo duplicated |

### microvm-racknerd

| Spec | Value |
|------|-------|
| OS | Debian (microVM) |
| Public IP | 172.245.19.182 |
| Disk | 9.1G, 6.4G free |
| Tailscale | 100.101.247.127 |
| Role | Caddy reverse proxy, public edge |
| Ports | 80, 443 open to internet |

### nixos-steamdeck-1

| Spec | Value |
|------|-------|
| OS | NixOS |
| Tailscale | 100.85.244.73 |
| Hostname | steamdeck |
| Role | GPU compute, planned edge LLM (3B-7B) |
| GPU | RDNA 2 |
| Status | just onboarded |

---

## Open Issues

| # | Issue | Node | Priority | Notes |
|---|-------|------|----------|-------|
| 1 | k3s Authentik PostgreSQL read-only filesystem | nixos-laptop | Low | Using standalone Podman instead |
| 2 | k3s Authentik Redis image pull failure | nixos-laptop | Low | Bitnami tags removed; Valkey already in use |
| 3 | 361395-1 APT 401 + duplicate repos | 361395-1 | Low | Cleanup `sources.list` when convenient |
| 4 | dracocomp offline | — | Low | Unreachable 3+ days |
| 5 | Garage S3 API only on qfox-1 localhost | qfox-1 | Low | Remote access via SSH tunnel or Tailscale funnel |
| 6 | Caddy admin API returns null certs JSON | racknerd | Info | Cert is functional; API introspection mismatch |

---

## Access Cheat Sheet

```bash
# SSH shortcuts (from ~/.ssh/config)
ssh nixos-laptop
ssh racknerd          # alias for microvm-racknerd
ssh 361395-1
ssh steamdeck          # nixos-steamdeck-1 (100.85.244.73)

# Tailscale direct
ssh -o StrictHostKeyChecking=accept-new root@100.110.163.82

# Authentik (local on nixos-laptop)
curl http://127.0.0.1:9000

# Caddy reload (on racknerd)
systemctl reload caddy

# Garage status
sudo /usr/local/bin/garage -c /etc/garage/garage.toml status

# Decrypt secrets
cd "/home/allaun/Research Stack"
sops --decrypt 4-Infrastructure/infra/secrets/credentials.json

# k3s on nixos-laptop
kubectl get pods -n services
kubectl get svc -n services

# restic backup (from qfox-1)
bash 4-Infrastructure/storage/restic/backup.sh full
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Redis replaced with Valkey in Authentik compose |
| 2026-05-22 | Caddy upstreams switched from k3s NodePort 30800 to standalone Podman 9000 |
| 2026-05-23 | **infra-controller** deployed on 361395-1 (Netcup); systemd timer every 5 min |
| 2026-05-23 | nixos-steamdeck-1 onboarded (100.85.244.73, NixOS, RDNA 2 GPU) |
| 2026-05-22 | nixos-laptop Tailscale IP changed 100.119.165.120 → 100.102.173.61 |

---

## Automation: infra-controller on 361395-1

The **infra-controller** is the central health orchestration daemon running on the Netcup VPS (361395-1). It probes all nodes every 5 minutes via SSH over the Tailscale mesh.

### Architecture

```
361395-1 (Netcup) — CONTROL PLANE
├── infra-controller.timer (systemd, every 5 min)
├── infra-controller.service (oneshot)
├── Receipts: ~/.cache/infra-controller.jsonl (hash-chained)
└── Alerting: local postfix → admin@researchstack.info

Probes (SSH → each node):
  qfox-1              → system, restic, garage, garage_buckets, gdrive_offload
  nixos-laptop        → system, k3s
  microvm-racknerd    → system, caddy
  nixos-steamdeck-1   → system
  361395-1 (local)    → system, garage, garage_buckets

Roles (affects alert severity):
  CRITICAL: microvm-racknerd, nixos-laptop  → alert on down
  OPTIONAL: qfox-1, nixos-steamdeck-1        → log only
```

### Receipts

- **Schema:** `infra_controller_receipt_v1`
- **Format:** JSONL hash-chain, one entry per cycle
- **Local:** `~/.cache/infra-controller.jsonl` (always available)
- **S3 backup:** planned (s3://research-stack/agent-receipts/)

### Commands

```bash
# Manual run
ssh 361395-1 "cd '/home/allaun/Research Stack' && python3 4-Infrastructure/auto/infra_controller.py --probe-only"

# View latest receipt
ssh 361395-1 "tail -1 ~/.cache/infra-controller.jsonl | python3 -m json.tool"

# Watch journal
ssh 361395-1 "journalctl -u infra-controller.service -f"

# Timer status
ssh 361395-1 "systemctl status infra-controller.timer"
```

### Code location

- `4-Infrastructure/auto/infra_controller.py` — main daemon
- `4-Infrastructure/auto/lib/probe.py` — SSH probe runner
- `4-Infrastructure/auto/lib/receipt.py` — receipt schema + hash-chain
- `4-Infrastructure/auto/lib/alerting.py` — email/webhook/dashboard dispatch
- `4-Infrastructure/auto/lib/config.py` — YAML config loader
- `4-Infrastructure/auto/config/nodes.yaml` — node inventory + thresholds
- `4-Infrastructure/auto/nodes/*.sh` — per-probe collector scripts (bash)

| 2026-05-21 | Wildcard TLS `*.researchstack.info` deployed via Porkbun DNS-01 |
| 2026-05-21 | Porkbun API keys regenerated and re-encrypted |
| 2026-05-20 | Garage cluster bumped to `replication_factor=3` across all nodes |
| 2026-05-20 | zram enabled cluster-wide |
| 2026-05-19 | NixOS flake conversion + k3s bootstrap on nixos-laptop |
| 2026-05-18 | Garage buckets created: research-stack, db-scratch, rds-overflow, snap-zone, gdrive-mirror |
