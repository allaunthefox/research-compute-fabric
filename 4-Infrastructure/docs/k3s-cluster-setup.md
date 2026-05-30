# k3s Cluster — Research Stack

**Schema:** `research-stack-k3s-cluster-v1`
**Date:** 2026-05-29
**Last updated:** 2026-05-30 (Ollama inference stack resolved)

---

## Cluster Topology

Single control plane on **cupfox**, workers on Neon-64GB, steamdeck, and racknerd. Cluster traffic runs over Tailscale mesh (bypasses netcup VPC firewall restrictions on port 6443).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Tailscale Mesh                                     │
│                                                                             │
│   cupfox (control-plane)         Neon-64GB (heavy worker)                  │
│   100.110.163.82                 100.64.19.78                             │
│   46.232.249.226                 152.53.81.164                            │
│   k3s API :6443                  k8s API traffic via Tailscale           │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                    k3s Cluster (cupfox)                        │     │
│   │                                                                 │     │
│   │   cupfox:6443 ──► etcd, API server, scheduler, controller     │     │
│   │                                                                 │     │
│   │   Workers (via Tailscale 100.x.x.x):                          │     │
│   │     • neon-64gb  — heavy stateful workloads                    │     │
│   │     • steamdeck   — GPU compute (RDNA 2)                       │     │
│   │     • racknerd    — edge services (Caddy TLS)                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│   nixos-laptop (100.102.173.61) — SEPARATE cluster, running full stack   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Nodes

| Node | Tailscale IP | Public IP | Role | Version | Arch | Labels |
|------|-------------|----------|------|---------|------|--------|
| cupfox | 100.110.163.82 | 46.232.249.226 | control-plane | v1.35.5 | amd64 | `node.kubernetes.io/workload=control-plane` |
| neon-64gb | 100.64.19.78 | 152.53.81.164 | worker (heavy) | v1.35.5 | arm64 | `worker=heavy,hpc=true,node.kubernetes.io/workload=heavy-stateful` |
| steamdeck | 100.85.244.73 | — | worker (gpu) | v1.34.5 | amd64 | `gpu=true,worker=gpu,node.kubernetes.io/workload=gpu-muscle` |
| racknerd | 100.80.39.40 | 172.245.19.182 | worker (edge) | v1.35.5 | amd64 | `worker=edge,node.kubernetes.io/workload=edge-service` |

### Hardware

| Node | CPU | RAM | Disk | Notes |
|------|-----|-----|------|-------|
| cupfox | 2 vCPU EPYC | 3.8 GB | 125 GB (86% used) | EPYC means 2 cores is capable for control plane |
| Neon-64GB | 18 vCPU ARM64 EPYC | 64 GB | 2 TB | Heavy workloads target |
| steamdeck | 8 vCPU AMD | 14.5 GB | — | RDNA 2 GPU (no NVIDIA driver) |
| racknerd | 1 vCPU Xeon | 715 MB | 9 GB | Edge only |

---

## Node Roles

### cupfox (control-plane)
- API server, etcd, scheduler, controller-manager
- Traefik ingress (disabled — use Caddy on racknerd)
- ServiceLB (disabled)
- ~2GB RAM for k8s control plane

### Neon-64GB (heavy worker)
Target for:
- Databases (PostgreSQL, etc.)
- Ollama inference (host-level, not k8s)
- Jellyfin, Sonarr, Radarr
- Authentik SSO (future)
- All PVCs (2TB local-path storage)
- ~20GB RAM currently used

### steamdeck (GPU worker)
Target for:
- Ollama / vLLM inference
- GPU compute workloads
- AlphaProof loop (if running)
- RDNA 2 GPU available

### racknerd (edge worker)
Target for:
- Caddy TLS termination (reverse proxy to Ollama and other services)
- Tailscale Funnel
- Lightweight edge services

---

## Deployment Commands

### Get cluster credentials
```bash
ssh root@cupfox "cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/config
# Or on any node with kubectl:
ssh root@cupfox "k3s kubectl get nodes"
```

### Check cluster status
```bash
ssh root@cupfox "k3s kubectl get nodes -o wide"
ssh root@cupfox "k3s kubectl get pods -A"
```

### Deploy workload to specific node
```bash
# Deploy to GPU node (steamdeck)
k3s kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test
spec:
  nodeSelector:
    worker: gpu
  containers:
  - name: cuda
    image: nvidia/cuda:12.0-base
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1
EOF
```

### Label a node
```bash
ssh root@cupfox "k3s kubectl label node <node> worker=<type> --overwrite"
```

---

## Agent Token

Current agent token (get fresh from cupfox):
```bash
ssh root@cupfox "cat /var/lib/rancher/k3s/server/agent-token"
```

---

## Storage

Local-path provisioner on all nodes. For PVCs, use Neon-64GB (2TB) or attach external storage.

---

## Network Policy

- Cluster internal: Tailscale network (100.x.x.x)
- External access: Caddy on racknerd → reverse proxy to appropriate service
- Public domains: `*.researchstack.info` via Caddy on racknerd

---

## Inference Serving (Ollama)

Ollama runs **directly on Neon-64GB host** (not in k8s), accessed via Caddy reverse proxy on racknerd. This avoids RAM pressure from KServe/Knative which required >4GB on cupfox.

### Architecture

```
curl http://100.80.39.40:8443/api/generate
    └── Caddy (:8443) ────► Neon-64GB (:11434)
         racknerd              host Ollama
    TLS termination           llama3.2:1b
```

### Current State

| Component | Node | Address | Status |
|-----------|------|---------|--------|
| Ollama (host) | Neon-64GB | `http://100.64.19.78:11434` | Running, `llama3.2:1b` loaded |
| Caddy proxy | racknerd | `http://100.80.39.40:8443` | Forwarding to 100.64.19.78:11434 |

### Verify Inference

```bash
# Direct to Ollama
curl -s http://100.64.19.78:11434/api/generate \
  -d '{"model":"llama3.2:1b","prompt":"hi","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"

# Via Caddy proxy
curl -s http://100.80.39.40:8443/api/generate \
  -d '{"model":"llama3.2:1b","prompt":"hi","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"

# List available models
curl -s http://100.80.39.40:8443/api/tags | python3 -c "import sys,json; print([m['name'] for m in json.load(sys.stdin)['models']])"
```

### Troubleshooting

**502 Bad Gateway from Caddy:** Caddy's `--resume` flag loads stale config from `/var/lib/caddy/caddy/autosave.json`. If the autosave points to a dead port, remove it and restart:
```bash
ssh root@100.80.39.40
systemctl stop caddy
rm -f /var/lib/caddy/caddy/autosave.json
systemctl start caddy
```

**passt intercepting port 11434:** If another process (passt for k8s service) grabs port 11434, delete the conflicting k8s deployment:
```bash
ssh root@46.232.249.226
k3s kubectl delete deployment ollama -n inference --force
k3s kubectl delete service ollama -n inference --force
```

**Duplicate Ollama processes:** Host-level Ollama runs as systemd service (`ollama.service`). Check with:
```bash
ssh root@152.53.81.164
systemctl status ollama --no-pager -n 3
ss -tlnp | grep 11434
```

### Caddy Config

On racknerd (`/etc/caddy/Caddyfile`):
```
{
	admin off
}

:8443 {
	reverse_proxy /api/* 100.64.19.78:11434
	reverse_proxy /* 100.64.19.78:11434
}

:8080 {
	respond "Ollama proxy running" 200
}
```

Note: Ensure `--resume` flag is NOT in the systemd unit (`/etc/systemd/system/caddy.service`) — Caddyfile is the source of truth.

---

## Notes

- **nixos-laptop** runs its own k3s cluster (100.102.173.61) with full workload stack. Not part of this cluster. Workloads: Authentik, Jellyfin, Sonarr, Radarr, Actual Budget, Vaultwarden, uptime-kuma.
- **steamdeck** on v1.34.5 (NixOS channel locked), compatible with v1.35.5 server.
- Cluster API reachable at `https://100.110.163.82:6443` (Tailscale only).
- Tailscale must be running on all nodes for cluster to function.
