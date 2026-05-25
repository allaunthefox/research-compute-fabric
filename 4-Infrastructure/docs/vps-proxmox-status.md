# Proxmox VPS Deployment Status

> **REALITY CHECK — 2026-05-21:** This document describes a historical state.
> The Netcup VPS (46.232.249.226) was reinstalled to **Debian 13** and now
> appears in Tailscale as **361395-1** (100.110.163.82). The Proxmox/LXC/Authentik
> stack described below no longer exists on this machine. The current state is:
> - OS: Debian 13 (OpenSSH_10.0p2 Debian-7+deb13u4)
> - Tailscale: 361395-1 / 100.110.163.82
> - SSH: key auth denied (needs root password or provider console recovery)
> - Public IP: 46.232.249.226 (netcup upstream filtering ports 80/443)
> Keep this file as archive only.

## Netcup VPS (46.232.249.226 / 2a03:4000:2b:468:980e:3bff:fea5:65aa)

### Completed

#### 1. Authentik in LXC 100
- **Container**: Debian 13, CT 100, `authentik` hostname
- **Network**: `192.168.100.100` on `vmbr0` with NAT/MASQUERADE for external IPv4
- **Services**: Docker, PostgreSQL 16, Redis
- **Authentik**: `ghcr.io/goauthentik/server:2025.4` running
  - Server on `192.168.100.100:9000`
  - Worker healthy
  - Default admin: `akadmin` / `authentik` (change on first login)

#### 2. Caddy Reverse Proxy
- **Binary**: Custom Caddy v2.11.3 with Porkbun DNS plugin at `/opt/caddy/caddy`
- **Service**: Enabled and running (`systemctl status caddy`)
- **Domains configured**:
  - `researchstack.info` -> Proxmox Web UI (`localhost:8006`)
  - `auth.researchstack.info` -> Authentik (`192.168.100.100:9000`)
- **DNS**: Porkbun A records updated to `46.232.249.226`
- **Certificates**: Let's Encrypt DNS-01 obtained for both domains

#### 3. Tailscale
- **Status**: Authenticated and active
- **Tailscale IP**: `100.110.163.82` (node: `361395-1`)
- **Mesh**: Can see `qfox-1`, `microvm-racknerd`, `nixos-laptop`, `dracocomp`
- **PQC**: Tailscale 1.98+ uses X25519Kyber768 hybrid key exchange automatically

#### 4. Post-Quantum Cryptography
- **SSH (VPS)**: `mlkem768x25519-sha256` explicitly configured and preferred in `sshd_config` and `ssh_config`
- **Tailscale**: Hybrid PQ already active
- **Document**: `4-Infrastructure/docs/pqc-posture.md`

#### 5. age / SOPS Secret Management
- **Keypair**: Generated at `~/.config/sops/age/keys.txt`
- **Public key**: `age1tp4vr565zkmvnyulatpyaj6z8zrz7q9mpaypz85yz8rty99crdasualxyr`
- **Encrypted files**:
  - `.env`
  - `4-Infrastructure/storage/restic/restic.env`
  - `4-Infrastructure/infra/secrets/credentials.json`
  - `4-Infrastructure/infra/secrets/appflowy.env`
  - `4-Infrastructure/infra/secrets/tailscale-auth.key`
  - `4-Infrastructure/deploy/cupfox/pre-infect-backup/porkbun.env`
  - `API KEYS/racknerd_510bd9c_root.txt`
  - `API KEYS/racknerd_solusvm_api.txt`
- **Config**: `.sops.yaml` at repo root; `4-Infrastructure/k3s-flake/.sops.yaml` updated

#### 6. Proxmox Backups
- **Schedule**: Daily at 03:00 CEST
- **Target**: `local` storage (zstd compressed)
- **Scope**: CT 100 (authentik)
- **Command to verify**: `pvesh get /cluster/backup`

#### 7. BraidRouter - Distributed Inference Mesh
- **Location**: LXC 100, Docker container `braid-router-braid-router-1`
- **Endpoint**: `http://192.168.100.100:9200/api/generate`
- **Caddy**: `braid.researchstack.info` (internal/Caddy), Tailscale serve `361395-1.tail4e7094.ts.net/braid/`
- **Topology**: 3-strand braid with Sidon labels (1, 2, 4)
- **Compute nodes**:
  | Node | Host | Port | Capacity | Status |
  |------|------|------|----------|--------|
  | `vps-local` | `192.168.100.1` | 11434 | 0.5 (small) | Online - Ollama on Proxmox host |
  | `qfox-1` | `100.88.57.96` | 11434 | 0.0 (offline) | Offline - no open SSH ports |
  | `nixos-laptop` | `192.168.100.1:11435` (proxied) | - | 1.5 (large) | Online - Ollama via socat proxy |
- **Proxy**: `ollama-nixos-proxy.service` on Proxmox host forwards `*:11435` -> `100.119.165.120:11434` via `socat`
- **Crossing matrix**: 50/50 split between `vps-local` and `nixos-laptop`
- **Test model**: `qwen2.5:0.5b` (397MB) deployed on both nodes
- **Verification**:
  ```bash
  curl -s -X POST http://192.168.100.100:9200/api/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Say hello", "options": {"model": "qwen2.5:0.5b"}}'
  ```

### Blockers

#### 1. Netcup Upstream Port Filtering
- **Symptom**: Ports 80, 443, and 8006 are unreachable from the public internet
- **Impact**: Caddy HTTPS and Proxmox Web UI are only accessible via:
  - SSH tunnel: `ssh -L 18006:localhost:8006 root@46.232.249.226`
  - Tailscale: `https://100.110.163.82:8006` (if Caddy is bypassed) or direct Tailscale access
- **Remediation options**:
  - Contact netcup support to open ports 80/443
  - Use Tailscale Funnel for public HTTPS access
  - Use a separate reverse proxy VPS with open ports

#### 2. Garage S3 Backup Integration
- **Symptom**: Garage S3 endpoint (`100.88.57.96:3900`) unreachable from VPS over Tailscale
- **Impact**: Proxmox backups cannot be offloaded to Garage S3 mesh
- **Root cause**: Garage on `qfox-1` binds S3 API to localhost only
- **Remediation options**:
  - Reconfigure Garage on `qfox-1` to bind `0.0.0.0:3900` or `100.88.57.96:3900`
  - Set up an SSH tunnel from VPS to `qfox-1` port 3900
  - Run a local Garage node on the VPS and join the cluster

### Access Cheat Sheet

```bash
# SSH to VPS
ssh root@46.232.249.226

# SSH tunnel to Proxmox Web UI
ssh -L 18006:localhost:8006 root@46.232.249.226
# Then open https://localhost:18006 in browser

# Access Authentik setup flow (via Tailscale or SSH tunnel to Caddy)
# Via Tailscale directly to LXC:
tailscale ssh root@361395-1
curl http://192.168.100.100:9000

# Decrypt secrets with sops
cd /home/allaun/Research Stack
sops --decrypt 4-Infrastructure/storage/restic/restic.env

# Edit encrypted secret
sops 4-Infrastructure/infra/secrets/credentials.json
```

### Next Steps

1. **Open netcup ports 80/443** or switch to Tailscale Funnel for public HTTPS
2. **Reconfigure Garage S3 binding** on `qfox-1` for Tailscale-accessible S3 endpoint
3. **Migrate Proxmox backups** from `local` to Garage S3 once connectivity is resolved
4. **Change Authentik default password** (`akadmin` / `authentik`) on first login
5. **Configure Authentik** as identity provider for Proxmox (OIDC)
6. **Reboot VPS** to activate `amd_pstate` and IOMMU (optional, if VM passthrough desired)
7. **Pull larger models** on `nixos-laptop` (e.g., `qwen2.5:7b`, `llama3.1:8b`) for heavier inference
8. **Fix qfox-1 access** - enable SSH or Tailscale SSH server on the node for Ollama deployment
9. **Install Tailscale in LXC 100** to eliminate the socat proxy hop for nixos-laptop
10. **Add `vps-local` Ollama to systemd** - currently running as manual `ollama serve` on Proxmox host
11. **Monitor BraidRouter** - consider adding health checks and automatic node failover
