# Unified Topology Flake — Research Stack

A zero-fingerprint NixOS flake that describes the entire k3s cluster topology as
code. Every node contains the seed to reconstruct itself: no IPs, no secrets,
no external dependencies embedded in the flake.

## Principle

> A node goes online → it joins → it goes offline → the cluster adjusts.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Internet                                                           │
│    ▼                                                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Public Edge (microvm-racknerd)                             │    │
│  │  Caddy: TLS termination only (Porkbun DNS-01)              │    │
│  │  Ports 80/443 → forwards ALL traffic over Tailscale        │    │
│  └───────────────────────────┬─────────────────────────────────┘    │
│                              │ Tailscale mesh                       │
│  ┌───────────────────────────▼─────────────────────────────────┐    │
│  │  Traefik Ingress (nixos-laptop / k3s-server :80)            │    │
│  │  Path routing + forward_auth middleware (Authentik)          │    │
│  │  Defined in manifests/ingress/ (Ingress + Middleware CRDs)  │    │
│  └───────────────────────────┬─────────────────────────────────┘    │
│                              │                                      │
│  ┌───────────────────────────▼─────────────────────────────────┐    │
│  │  k3s Service Layer (ClusterIP)                              │    │
│  │  Hermes, Authentik, Uptime Kuma, Homarr, control-plane APIs │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Worker Pool (qfox-1, steamdeck, 361395-1, ...)             │    │
│  │  GPU compute, storage, downloaders, codecs                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## URL Contract (canonical paths on `https://researchstack.info`)

| Path | Service | Type |
|------|---------|------|
| `/` | Homer directory | Dashboard |
| `/gettingstarted` | Static page | Info |
| `/apps/chat/*` | Hermes (chat/orchestrator) | App |
| `/apps/jellyfin/*` | Jellyfin | App |
| `/apps/books/*` | Audiobookshelf | App |
| `/apps/music/*` | Navidrome | App |
| `/apps/budget/*` | Actual Budget | App |
| `/server/status/*` | Uptime Kuma | Ops UI |
| `/server/dash/*` | Homarr | Ops UI |
| `/server/vault/*` | Vaultwarden | Ops UI |
| `/api/cred/*` | Credential Server | Control-plane |
| `/api/registry/*` | Registry API (join/heartbeat) | Control-plane |
| `/api/jobs/*` | Job Router | Control-plane |
| `/api/blobs/*` | Blob Plane | Control-plane |

**Stable subdomains** (not path-routed):
- `auth.researchstack.info` → Authentik (OIDC issuer — must not change)
- `mail.researchstack.info` / `webmail.researchstack.info` → Mail services

**Legacy subdomain redirects** (301 → canonical path):
- `status.*` → `/server/status/`
- `dash.*` / `home.*` → `/`
- `media.*` → `/apps/jellyfin/`
- `books.*` → `/apps/books/`
- `music.*` → `/apps/music/`
- `vault.*` → `/server/vault/`
- `apps.*` → `/apps/`
- `pulse.*` → `/api/registry/`

## File Layout

```
4-Infrastructure/k3s-flake/
├── flake.nix                    — 6 topology configurations
├── k3s-configuration.nix       — base module (Tailscale, SSH, Nix, firewall, sops)
├── k3s-server.nix              — control plane + Traefik Ingress + deploy oneshot
├── k3s-edge.nix                — public TLS edge (Caddy) + mail services
├── .sops.yaml                  — age key rules
├── secrets/                    — encrypted at rest, decrypted at activation
│   ├── k3s-token.age           — K3S_TOKEN=<value>
│   ├── authentik-secrets.age   — secret-key, postgresql-password
│   └── porkbun-env.age         — PORKBUN_API_KEY, PORKBUN_SECRET_KEY
├── roles/                      — one module per topology role
│   ├── core.nix                — label: topology.researchstack.io/role=core
│   ├── judge.nix               — label: role=judge
│   ├── mirror.nix              — label: role=mirror
│   ├── edge.nix                — label: role=edge, taint: pulse-only:NoSchedule
│   └── foxtop.nix              — label: role=foxtop
├── manifests/                  — Kubernetes resources, auto-deployed by systemd
│   ├── kustomization.yaml      — master resource list
│   ├── namespace.yaml          — namespace: services
│   ├── ingress/                — Traefik Ingress + Middleware CRDs (path routing)
│   ├── authentik/              — HelmChart CRD (OIDC @ auth.researchstack.info)
│   ├── hermes/                 — Deployment + ClusterIP (placeholder → /apps/chat/)
│   ├── credential-server/      — Deployment + ClusterIP (/api/cred/*)
│   ├── control-plane/          — Registry, Jobs, Blobs APIs (/api/*)
│   ├── uptime-kuma/            — Deployment + Service (/server/status/)
│   ├── homer/                  — Deployment + Service (/)
│   ├── homarr/                 — Deployment + Service (/server/dash/)
│   ├── actual-budget/          — Deployment + Service (/apps/budget/)
│   ├── vaultwarden/            — Deployment + Service (/server/vault/)
│   ├── media/                  — Jellyfin, Navidrome, Audiobookshelf, *arr stack
│   ├── heimdall/               — [LEGACY] being replaced by path routing
│   └── pulse-receiver/         — [LEGACY] being replaced by /api/registry/
└── scripts/
    └── deploy-services.sh      — idempotent kubectl apply, called by systemd oneshot
```

## Topology Design

### Roles & Node Classes

| Role    | k3s Label                                       | Taints                    | Workload |
|---------|-------------------------------------------------|---------------------------|----------|
| server  | — (control plane)                               | —                         | Internal Caddy router + deploy-manifests |
| core    | `topology.researchstack.io/role=core`           | —                         | General compute (PG, Redis, Authentik) |
| judge   | `topology.researchstack.io/role=judge`          | —                         | Validation / audit |
| mirror  | `topology.researchstack.io/role=mirror`         | —                         | Storage / replication |
| edge    | `topology.researchstack.io/role=edge`           | `pulse-only:NoSchedule`   | Public TLS edge + mail |
| foxtop  | `topology.researchstack.io/role=foxtop`         | —                         | Primary compute / orchestrator |

### Service Placement

| Service            | Port  | Path              | Prefers Role | Stateful? |
|--------------------|-------|-------------------|--------------|-----------|
| Authentik          | 80    | auth.* subdomain  | core         | Yes (PG + Redis PVCs) |
| Hermes             | 80    | /apps/chat/       | any          | No (placeholder) |
| Uptime Kuma        | 3001  | /server/status/   | any          | PVC (1Gi) |
| Homer              | 8080  | /                 | any          | No (ConfigMap) |
| Homarr             | 7575  | /server/dash/     | any          | PVC |
| Actual Budget      | 5006  | /apps/budget/     | any          | PVC |
| Vaultwarden        | 80    | /server/vault/    | any          | PVC |
| Credential Server  | 8444  | /api/cred/        | any          | Secret vol |
| Registry API       | 8080  | /api/registry/    | any          | No (stub) |
| Jobs API           | 8080  | /api/jobs/        | any          | No (stub) |
| Blobs API          | 8080  | /api/blobs/       | any          | No (stub) |

All services use ClusterIP and are routed via Traefik Ingress. Legacy
NodePort assignments are preserved for backward compat but are not the
primary routing path.

### Routing Model (Caddy edge + Traefik Ingress)

**Public edge** (`k3s-edge.nix` / microvm-racknerd):
- Caddy terminates TLS via Porkbun DNS-01 wildcard
- Forwards all traffic to Traefik (`100.102.173.61:80`) over Tailscale
- Handles legacy subdomain 301 redirects at the edge
- `auth.*` and `mail.*`/`webmail.*` forwarded with Host header preserved

**Traefik Ingress** (k3s built-in, nixos-laptop):
- Listens on `:80` (node port, HTTP — TLS handled by edge)
- Path-based routing defined in `manifests/ingress/ingress.yaml`
- Traefik Middleware CRDs for:
  - `authentik-forward-auth` — SSO gate for `/apps/*`, `/server/*`, `/`
  - `strip-*` — prefix stripping per route
- `/api/*` routes skip `forward_auth` (token-authenticated)
- `auth.researchstack.info` matched by separate Ingress (no middleware)

TLS via Porkbun DNS challenge (caddy-dns/porkbun plugin) at the edge.

## Node Lifecycle

| Phase     | What happens |
|-----------|-------------|
| **Goes online** | NixOS activates → sops decrypts secrets → Tailscale connects → k3s agent starts → joins cluster via `serverAddr` (Tailscale DNS) |
| **Joins**   | Token validated from `K3S_TOKEN` env var (sops-decrypted) → node registers with topology label |
| **Goes offline** | kubelet stops heartbeating → k8s marks `NotReady` (40s grace) → pods evicted (5m) |
| **Adjusts**  | Remaining nodes reschedule evicted pods; returning node re-registers and re-accepts workloads |
| **Reconstructs** | Any node rebuilt from the flake alone — secrets decrypt via sops, no other machine required |

## Bootstrap Workflow

### 1. Prerequisites

- A machine running NixOS (or Nix installed) to build the flake
- Age key pair for sops (`age-keygen -o ~/.config/sops/age/keys.txt`)
- Porkbun API key + secret for TLS
- Tailscale auth key (optional — first `tailscale up` can be manual)

### 2. Generate & Encrypt Secrets

```bash
# Generate k3s token
TOKEN=$(openssl rand -hex 32)
echo "K3S_TOKEN=$TOKEN" | age -e -r "$(cat ~/.config/sops/age/keys.txt | age-key -y)" \
  -o 4-Infrastructure/k3s-flake/secrets/k3s-token.age

# Generate authentik secrets
cat > /tmp/authentik.env << EOF
secret-key=$(openssl rand -hex 32)
postgresql-password=$(openssl rand -hex 16)
EOF
age -e -r "$(cat ~/.config/sops/age/keys.txt | age-key -y)" \
  -o 4-Infrastructure/k3s-flake/secrets/authentik-secrets.age < /tmp/authentik.env
rm /tmp/authentik.env

# Encrypt porkbun credentials
echo "PORKBUN_API_KEY=your_key
PORKBUN_SECRET_KEY=your_secret" | \
age -e -r "$(cat ~/.config/sops/age/keys.txt | age-key -y)" \
  -o 4-Infrastructure/k3s-flake/secrets/porkbun-env.age
```

### 3. Configure `.sops.yaml`

```yaml
keys:
  - &admin age1yourpublickey...
creation_rules:
  - path_regex: secrets/.*\.age$
    key_groups:
      - age:
          - *admin
```

### 4. Fill in `flake.nix`

Edit the 6 `nixosConfigurations` entries:

```nix
k3s-server = mkNode {
  hostName = "k3s-server";
  domain = "researchstack.info";
  extraModules = [ ./k3s-server.nix ];
};

k3s-core = mkNode {
  hostName = "k3s-core-1";
  serverAddr = "https://k3s-server.tail-XXXXX.ts.net:6443";
  extraModules = [ ./roles/core.nix ];
};
# ... repeat for judge, mirror, edge, foxtop
```

### 5. Add SSH Keys

In `k3s-configuration.nix`:

```nix
users.users.root.openssh.authorizedKeys.keys = [
  "ssh-ed25519 AAAAC3... your-key-comment"
];
```

### 6. Deploy

```bash
# Server first
nixos-rebuild switch --flake .#k3s-server --target-host root@<server-ip>

# Then agents — they auto-join via Tailscale
nixos-rebuild switch --flake .#k3s-core --target-host root@<core-ip>
nixos-rebuild switch --flake .#k3s-edge --target-host root@<microvm-nerdrack-ip>
# ... etc

# Verify
kubectl get nodes --show-labels
kubectl get pods -n services
```

## Service Details

### Authentik

- Deployed via k3s HelmChart CRD (official authentik Helm chart)
- In-cluster PostgreSQL (8Gi PVC) and Redis (2Gi PVC)
- NodePort 30800, routes to `auth.YOUR_DOMAIN`
- DB password and secret key from sops-decrypted K8s Secret
- Affinity: prefers `core` and `server` nodes

### Pulse Receiver

Minimal Python HTTP server deployed as a single pod:

```
POST /<node-name>   → records pulse timestamp
GET /               → returns JSON map of all pulse timestamps
```

The microvm-nerdrack (edge role, `pulse-only:NoSchedule` taint) cannot run
workloads but is monitored via its kubelet heartbeat. External edge devices
(such as an ESP32) can `POST /esp32-pulse-1` to `pulse.YOUR_DOMAIN:30804`.

### Homer Dashboard

Pre-configured with links to:
- Authentik (`https://auth.YOUR_DOMAIN`)
- Uptime Kuma (`https://status.YOUR_DOMAIN`)
- Heimdall (`https://apps.YOUR_DOMAIN`)
- Pulse Receiver (`https://pulse.YOUR_DOMAIN`)

Edit `manifests/homer/configmap.yaml` to update links.

## Storage Considerations

- Default k3s `local-path` provisioner — PVCs are node-bound
- **Stateless workloads** (Homer, Pulse Receiver) reschedule freely
- **Stateful workloads** (Authentik PG/Redis, Uptime Kuma, Heimdall) stay on
  their assigned node until the PVC is manually moved
- For true "adjusts" with stateful workloads, add Longhorn or another
  distributed storage provisioner

## Scaling

| Direction | Action |
|-----------|--------|
| Add a node | Write a new `nixosConfigurations` entry in `flake.nix`, deploy |
| Remove a node | `kubectl drain <node>`, delete config, stop the machine |
| Promote a role | Change `extraModules` in `flake.nix`, redeploy |
| Demote a role | Same — the flake is the source of truth |

## Zero-Fingerprint Guarantee

The flake contains **no**:

- IP addresses (all `127.0.0.1` or parameterized)
- Domain names (parameterized via `specialArgs.domain`)
- Machine identifiers (hostnames are `specialArgs`)
- API keys or tokens (all in sops-encrypted `.age` files)
- SSH keys (user fills in `k3s-configuration.nix`)
- Tailscale auth keys (manual `tailscale up` or external file)

Every deployment-specific value comes from:
- `specialArgs` at build time
- Sops-decrypted `.age` files at activation time
- The user's configuration edits in `flake.nix`
