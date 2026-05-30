# Infrastructure Status — Research Stack

> **Last verified:** 2026-05-30
> **Scope:** All live nodes, services, and storage in the Tailscale mesh.

---

## Cluster Overview

All nodes run k3s v1.35.5+k3s1 (except steamdeck: v1.34.5+k3s1) joined into a single cluster,
networked over Tailscale. cupfox is the control-plane; all other nodes are workers.

**kubeconfig:** retrieve from cupfox at `/etc/rancher/k3s/k3s.yaml` (replace `0.0.0.0` → `100.110.163.82` for Tailscale access).

```bash
# Access cluster from anywhere via Tailscale
ssh root@100.110.163.82 'cat /etc/rancher/k3s/k3s.yaml' | sed 's|0.0.0.0|100.110.163.82|g' > ~/.kube/config
kubectl get nodes
```

| Node | k3s Role | CPU | RAM | Arch | Public IP | Tailscale | Notes |
|------|----------|-----|-----|------|-----------|-----------|-------|
| cupfox | control-plane | 2 | 3.8 GiB | amd64 | 46.232.249.226 | 100.110.163.82 | k3s + KubeRay operator |
| neon-64gb | worker | 18 | 62.7 GiB | **arm64** | 152.53.81.164 | 100.100.75.113 | Heavy stateful + inference |
| racknerd | worker | 1 | 715 MiB | amd64 | 172.245.19.182 | 100.80.39.40 | TLS via Caddy, too small for Ray |
| steamdeck | worker | 8 | 14.5 GiB | amd64 | — | 100.85.244.73 | NixOS 25.11, Ray head + worker running |

> **Note:** neon-64gb is ARM64 — `rayproject/ray` images are amd64 only. Build or pull multi-arch
> images to use its 18 cores. Racknerd has only 715 MiB RAM and cannot run Ray pods.

---

## k3s Cluster — cupfox

k3s v1.35.5+k3s1 runs as control-plane on cupfox. Flannel.1 (mtu 1280) handles pod networking.

### System pods

| Pod | Ready | Node | Status |
|-----|-------|------|--------|
| coredns-6b6544b569-n86sp | 1/1 | steamdeck | Running |
| local-path-provisioner-5d9d9885bc-5hbt2 | 1/1 | cupfox | Running |
| metrics-server-56dd944747-g59vn | 1/1 | steamdeck | Running |

### Ray on k3s — KubeRay Operator

| Component | Version | Namespace | Status |
|-----------|---------|-----------|--------|
| kuberay-operator | 1.6.1 | ray-system | Running |
| raycluster (head) | 2.40.0 | ray-system | Running on steamdeck |
| raycluster (worker) | 2.40.0 | ray-system | Running on steamdeck |

```bash
# Check Ray status
kubectl exec -it raycluster-head-xxx -n ray-system -- ray status

# Ray Python test
kubectl exec -it raycluster-head-xxx -n ray-system -- python -c "import ray; ray.init(); print(ray.cluster_resources())"
```

**RayCluster manifest:** `4-Infrastructure/kube/raycluster.yaml`

---

## Storage: Garage S3

Garage v2.3.0 — self-hosted S3-compatible object store, Tailscale-only access.

### Cluster Topology

| Node | Tailscale IP | Address | Capacity | DataAvail |
|------|-------------|---------|----------|-----------|
| cupfox | 100.110.163.82 | — | 68.9 GiB | 65.2 GiB (52.3%) |
| qfox-1 (local) | 100.88.57.96 | — | 780.4 GiB | 1.5 TiB (83.5%) |
| nixos-laptop | 100.102.173.61 | — | 346.5 GiB | 393.5 GiB (85.8%) |

- **Replication factor:** 3
- **Layout version:** 1

### Ports

| Port | Purpose | Binding |
|------|---------|---------|
| 3900 | S3 API | qfox-1 localhost + Tailscale |
| 3901 | RPC | all nodes, Tailscale-only |
| 3903 | Admin API | loopback only |

### Buckets

| Bucket | Purpose |
|--------|---------|
| `research-stack` | Primary project objects |
| `db-scratch` | Active SQLite scratch DBs |
| `rds-overflow` | pg_dump / COPY TO exports |
| `snap-zone` | ZFS send/receive snapshots |
| `gdrive-mirror` | Mirror of gdrive:research-stack |

### Scripts

| Script | Purpose |
|--------|---------|
| `backup.sh snap [tag]` | Snapshot repo tree → Garage |
| `backup.sh snap-db [dir]` | Snapshot SQLite scratch DBs |
| `backup.sh cold-copy` | rclone copy Garage → gdrive:restic-mirror |
| `backup.sh forget` | Retention prune (7d/4w/6m) |
| `backup.sh verify` | restic check --read-data-subset=5% |
| `backup.sh full` | snap + cold-copy + sync-gdrive + forget |

Daily timer fires at 03:00 ±30 min. Post-commit hook runs `db-consolidate.sh offload + consolidate` async.

---

## Public Edge: Caddy on racknerd

Caddy handles TLS termination for `*.researchstack.info` domains.

### Domains & Routing

| Domain | Upstream | Notes |
|--------|----------|-------|
| `researchstack.info` | 100.102.173.61:30803 | Homer dashboard |
| `dash.researchstack.info` | 100.102.173.61:30802 | Heimdall |
| `status.researchstack.info` | 100.102.173.61:30801 | Uptime Kuma |
| `auth.researchstack.info` | 100.102.173.61:9000 | Authentik SSO (direct) |

### TLS

- **Certificate:** `*.researchstack.info` + `researchstack.info`
- **Issuer:** Let's Encrypt
- **Challenge:** DNS-01 via Porkbun API
- **Valid:** 2026-05-21 → 2026-08-19

---

## Services by Node

### cupfox (100.110.163.82)
- k3s control-plane
- KubeRay operator (ray-system namespace)
- Garage storage node (fra zone)

### neon-64gb (100.100.75.113)
- k3s worker (ARM64, 18 cores)
- Docker: ollama, cert-manager, knative (no Ray images available for ARM64)
- **Note:** Ray images must be built/pulled for linux/arm64 to use GPU workers here

### racknerd (100.80.39.40)
- k3s worker (715 MiB RAM — too small for Ray)
- Docker: docker-mailserver
- Caddy TLS termination

### steamdeck (100.85.244.73)
- k3s worker (NixOS 25.11, 8 cores, 14 GiB RAM)
- Docker: nginx, postgres, ollama, authentik, homarr, audiobookshelf, roundcube
- Ray head + worker running on this node

### nixos-laptop (100.102.173.61)
- Authentik SSO (standalone Podman, port 9000)
- Uptime Kuma, Heimdall, Homer (k3s NodePorts)
- Garage storage node (ord zone)
- SSH access via Tailscale key

### qfox-1 (this machine, 100.88.57.96)
- Primary Garage S3 endpoint
- Build host (CUDA 13.2, RTX, 30 GiB RAM)
- Local Nix environment

---

## Post-Quantum Cryptography

| Layer | Status |
|-------|--------|
| **Tailscale** | X25519Kyber768 hybrid key exchange active (v1.98+) |
| **SSH (all nodes)** | `mlkem768x25519-sha256` preferred |
| **Garage RPC** | Tailscale transport only |

---

## Access Cheat Sheet

```bash
# Cluster admin (via Tailscale)
ssh root@100.110.163.82 'cat /etc/rancher/k3s/k3s.yaml' | sed 's|0.0.0.0|100.110.163.82|g' > /tmp/kubeconfig
KUBECONFIG=/tmp/kubeconfig kubectl get pods -n ray-system

# Ray status
KUBECONFIG=/tmp/kubeconfig kubectl exec -it raycluster-head-xxx -n ray-system -- ray status

# SSH shortcuts (from ~/.ssh/config)
ssh root@100.110.163.82   # cupfox
ssh root@152.53.81.164    # neon-64gb
ssh root@172.245.19.182   # racknerd
ssh root@100.85.244.73    # steamdeck

# Garage status (local)
garage status

# Decrypt secrets
sops --decrypt 4-Infrastructure/infra/secrets/credentials.json
```

---

## Open Issues

| # | Issue | Node | Priority |
|---|-------|------|----------|
| 1 | neon-64gb ARM64 — no Ray images available | neon-64gb | High |
| 2 | Dependabot alert #75 (`@ai-sdk/provider-utils`, transitive) | — | Low |
| 3 | racknerd RAM too small for Ray (715 MiB) | racknerd | Won't fix |
| 4 | CUDA driver mismatch (610.x vs 13.2 toolkit) — needs reboot | qfox-1 | Medium |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-30 | k3s cluster migrated to cupfox (was nixos-laptop); kubeconfig accessible via Tailscale |
| 2026-05-30 | KubeRay operator 1.6.1 deployed in ray-system namespace |
| 2026-05-30 | RayCluster deployed: head + worker on steamdeck (2 CPUs total) |
| 2026-05-30 | Node naming standardized: cupfox / neon-64gb / racknerd / steamdeck |
