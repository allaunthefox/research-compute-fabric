# Deployment Plan: Path-Based Routing with Traefik Ingress

## Overview

This document describes the **safe, staged deployment** of path-based routing via Traefik Ingress, with host Caddy as a stable fallback during migration. This follows the principle: **change one routing layer at a time**.

### Current Architecture

```
Internet → edge Caddy (racknerd:443, TLS) → host Caddy (nixos:80, NodePort router) → Services
```

- **edge Caddy** (microvm-racknerd): TLS termination via Porkbun DNS-01, forwards to `100.102.173.61:80`
- **host Caddy** (nixos-laptop): HTTP only, NodePort-based routing to services
- **k3s**: nixos-laptop is currently an **agent** node (joins cupfox control-plane)
- **Traefik**: NOT running (disabled or not present)

### Target Architecture

```
Internet → edge Caddy (racknerd:443, TLS) → host Caddy (nixos:80, forwarder) → Traefik (nixos:30080, Ingress) → Services
```

- **edge Caddy** (microvm-racknerd): TLS termination, forwards to `100.102.173.61:80` (unchanged)
- **host Caddy** (nixos-laptop): HTTP only, forwards ALL to `127.0.0.1:30080` (Traefik)
- **k3s**: nixos-laptop becomes a **server** node, runs Traefik
- **Traefik**: Listens on NodePort 30080 (web), handles path-based routing + forward_auth

### Key Design Decisions

1. **Host Caddy stays as fallback**: Provides stable HTTP entrypoint during Traefik bringup
2. **Traefik on port 30080**: Avoids conflict with host Caddy on :80
3. **NodePort-based forwarding**: host Caddy → localhost:30080 (no DNS, no network hops)
4. **Ray support**: Ray cluster in `ray-system` namespace, dashboard at `/server/ray`
5. **VCN/LUPINE support**: Separate daemons on GPU nodes, not managed by k3s

---

## Files Changed

### 1. `k3s-server.nix` — NixOS Server Node with Traefik

**Changes:**
- Changed `services.k3s.role` from `"agent"` to `"server"`
- Removed `--disable=traefik` (Traefik is enabled by default)
- Added **host Caddy** configuration that forwards to Traefik on `127.0.0.1:30080`
- Added **Traefik NodePort assignment** service (ensures web=30080, websecure=30443)
- Added **deploy manifests** systemd service (applies kustomize manifests after k3s starts)
- Added **Ray namespace creation** service (ensures `ray-system` exists)
- Updated firewall to allow Traefik (30080), Ray (8265, 6379), and VCN (14834 UDP) ports
- k3s API moved to port 30443 to avoid conflicts

**Host Caddy routes:**
- `researchstack.info` → Traefik (all paths)
- `auth.researchstack.info` → Traefik (OIDC issuer)
- `mail.*`, `webmail.*` → Traefik (future mail Ingress)
- Legacy subdomain redirects (status, dash, home, media, books, music, vault, pulse, apps, chat, budget, www, ray)
- Wildcard fallback → root

### 2. `manifests/ingress/kustomization.yaml` — Include Ray Ingress

**Added:**
```yaml
resources:
  - middleware.yaml
  - ingress.yaml
  - ray-ingress.yaml  # NEW
```

### 3. `manifests/ingress/middleware.yaml` — Ray Middleware

**Added:**
```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: strip-server-ray
  namespace: ray-system
spec:
  stripPrefix:
    prefixes:
      - /server/ray
```

### 4. `manifests/ingress/ray-ingress.yaml` — Ray Dashboard Routing

**Updated:** Removed duplicate Middleware definition (now in middleware.yaml), kept IngressRoute that routes `/server/ray` → `raycluster-head-svc:8265` with stripPrefix middleware.

---

## Deployment Phases

### Phase 0: Pre-Deployment Checklist

- [ ] Verify cupfox (100.110.163.82) is healthy as control-plane
- [ ] Verify nixos-laptop (100.102.173.61) is currently an agent node
- [ ] Verify Tailscale connectivity between all nodes
- [ ] Verify edge Caddy (racknerd) can reach `100.102.173.61:80`
- [ ] Backup current k3s-server.nix and k3s-edge.nix
- [ ] Ensure SOPS key is available on nixos-laptop (`/var/lib/sops-nix/key.txt`)
- [ ] Verify k3s token exists (`secrets/k3s-token.age`)

### Phase 1: Deploy k3s-server (Internal Only)

**Goal:** Enable Traefik on nixos-laptop without affecting public traffic.

```bash
# On a machine with the repo checked out:
cd /home/allaun/repo/4-Infrastructure/k3s-flake

# 1. Copy files to nixos-laptop
ssh root@100.102.173.61 "mkdir -p /etc/nixos/k3s-flake/manifests"
rsync -av --delete manifests/ root@100.102.173.61:/etc/nixos/k3s-flake/manifests/
rsync -av flake.nix flake.lock k3s-server.nix k3s-configuration.nix roles/ secrets/ scripts/ \
  root@100.102.173.61:/etc/nixos/k3s-flake/

# 2. Rebuild nixos-laptop
ssh root@100.102.173.61 "cd /etc/nixos/k3s-flake && nixos-rebuild switch --flake .#k3s-server"
```

**Expected behavior:**
- nixos-laptop becomes a k3s **server** node (in addition to cupfox)
- Traefik starts and gets NodePort 30080 assigned
- Host Caddy starts on :80 and forwards to Traefik
- All existing services continue to work (NodePort routing still works)
- New Ingress routes are NOT yet active (manifests not applied)

**Verification:**
```bash
# From any tailnet node, test host Caddy forwarding:
curl -H "Host: researchstack.info" http://100.102.173.61/
# Should return 404 from Traefik (no routes configured yet)

# Check Traefik is running:
curl http://100.102.173.61:30080/
# Should return 404 from Traefik

# Check k3s nodes:
ssh root@100.102.173.61 "kubectl get nodes -o wide"
# Should show nixos-laptop as Ready, role=server

# Check Traefik service:
ssh root@100.102.173.61 "kubectl -n kube-system get svc traefik"
# Should show NodePort 30080 for web
```

**Rollback:** If Traefik doesn't start or breaks existing services:
```bash
# Revert to agent-only mode (remove Traefik, keep host Caddy)
ssh root@100.102.173.61 "nixos-rebuild switch --rollback"
```

### Phase 2: Apply Ingress Manifests

**Goal:** Deploy path-based routing, forward_auth, and Ray Ingress.

```bash
# The deploy-k3s-services systemd service should have auto-applied manifests.
# Verify:
ssh root@100.102.173.61 "kubectl get ingress -n services"
ssh root@100.102.173.61 "kubectl get middleware -n services"
ssh root@100.102.173.61 "kubectl get ingressroute -n ray-system"

# If not auto-applied, apply manually:
ssh root@100.102.173.61 "kubectl apply -k /etc/nixos/k3s-flake/manifests/"
```

**Verification:**
```bash
# Test Traefik routing internally (bypassing edge Caddy):
curl -H "Host: researchstack.info" http://100.102.173.61:30080/
# Should redirect to Authentik (302) or serve Homer

curl -H "Host: researchstack.info" http://100.102.173.61:30080/server/ray
# Should return Ray dashboard or 502 (if Ray not running)

curl -H "Host: auth.researchstack.info" http://100.102.173.61:30080/
# Should serve Authentik login page
```

### Phase 3: Deploy Service Pods

**Goal:** Deploy the new services (hermes, credential-server, control-plane APIs).

The manifests are already included in `kustomization.yaml`:
- hermes (chat)
- credential-server
- control-plane (registry, jobs, blobs APIs)
- actual-budget
- vaultwarden

**Apply:**
```bash
# Already done by deploy-k3s-services, but verify:
ssh root@100.102.173.61 "kubectl get pods -n services -o wide"
```

**Expected:** All pods should be Running (or Pending if storage not available).

### Phase 4: Internal End-to-End Testing

**Test all paths via Traefik directly (port 30080):**

```bash
# Landing page
curl -H "Host: researchstack.info" http://100.102.173.61:30080/ | grep -i "homer\|authentik"

# SSO-protected paths (should redirect to Authentik)
curl -H "Host: researchstack.info" http://100.102.173.61:30080/apps/chat/ -I | grep "Location.*auth"
curl -H "Host: researchstack.info" http://100.102.173.61:30080/server/status/ -I | grep "Location.*auth"

# API paths (should NOT redirect, return health or 502)
curl -H "Host: researchstack.info" http://100.102.173.61:30080/api/cred/ -I | grep -v "Location.*auth"
curl -H "Host: researchstack.info" http://100.102.173.61:30080/api/registry/health

# Ray dashboard
curl -H "Host: researchstack.info" http://100.102.173.61:30080/server/ray -I

# Auth subdomain
curl -H "Host: auth.researchstack.info" http://100.102.173.61:30080/ | grep -i "authentik"
```

**Expected results:**
- `/`, `/apps/*`, `/server/*` → 302 to Authentik (SSO gate)
- `/api/*` → 200 or 502 (no redirect, token-auth)
- `/server/ray` → Ray dashboard or 502
- `auth.*` → Authentik login page

### Phase 5: Deploy k3s-edge (Public Traffic)

**Goal:** Switch public traffic to the new routing stack. **This is the point of no return for public traffic.**

```bash
# Copy updated files to edge node
rsync -av flake.nix flake.lock k3s-edge.nix k3s-configuration.nix roles/ secrets/ \
  root@100.101.247.127:/etc/nixos/k3s-flake/

# Rebuild edge
ssh root@100.101.247.127 "cd /etc/nixos/k3s-flake && nixos-rebuild switch --flake .#k3s-edge"
```

**Expected behavior:**
- Public HTTPS traffic flows: edge Caddy (TLS) → host Caddy (:80) → Traefik (:30080) → Services
- All legacy subdomain redirects continue to work (defined at both edge and host Caddy)
- Path-based routing is active for public traffic

**Verification:**
```bash
# Quick smoke tests from external network (or via curl with public IP):
curl -sI https://researchstack.info/ | head -5
curl -sI https://auth.researchstack.info/ | head -5
curl -sI https://status.researchstack.info/ | head -5  # should 301

# Or run the full Playwright test suite:
cd /home/allaun/repo/4-Infrastructure/k3s-flake/tests
npm test
```

**Rollback:** If public traffic breaks:
```bash
ssh root@100.101.247.127 "nixos-rebuild switch --rollback"
# Edge will revert to old config (forwards to nixos-laptop:80)
# Host Caddy on nixos-laptop is still forwarding to Traefik
# So public traffic will still hit Traefik (which is fine)
# To fully rollback, also revert k3s-server on nixos-laptop
```

### Phase 6: Post-Deployment

**Run full E2E test suite:**
```bash
cd /home/allaun/repo/4-Infrastructure/k3s-flake/tests
npm test
# Target: All tests passing (40/40)
```

**Verify Ray dashboard:**
- Access https://researchstack.info/server/ray in browser
- Should show Ray cluster dashboard

**Verify VCN/LUPINE:**
- On GPU nodes (qfox-1, steamdeck), verify daemons are running:
  ```bash
  systemctl status vcn-lupine-daemon
  ```
- Verify LD_PRELOAD shim is in place:
  ```bash
  ls -la /opt/vcn-lupine/lib/libcuda.so.1
  ```

---

## Ray Cluster Integration

### Current State
- Ray cluster is **already running** in `ray-system` namespace (per README)
- Ray was deployed separately via KubeRay operator
- Ray dashboard service: `raycluster-head-svc:8265`

### Ingress Configuration
- **Path:** `/server/ray`
- **Middleware:** `strip-server-ray` (strips `/server/ray` prefix)
- **Service:** `raycluster-head-svc:8265`
- **Type:** Traefik IngressRoute (CRD, not standard Ingress)

### Verification Commands

```bash
# Check Ray pods
kubectl -n ray-system get pods

# Check Ray services
kubectl -n ray-system get svc

# Check IngressRoute
kubectl -n ray-system get ingressroute

# Test Ray dashboard access
kubectl -n ray-system port-forward svc/raycluster-head-svc 8265:8265
# Then access http://localhost:8265
```

### Future: Ray Operator

If Ray needs to be redeployed, use KubeRay:

```bash
# Install KubeRay operator
kubectl apply -f https://raw.githubusercontent.com/ray-project/kuberay/master/manifests/cluster-scoped-resources.yaml
kubectl apply -f https://raw.githubusercontent.com/ray-project/kuberay/master/manifests/namespaced-resources.yaml

# Deploy Ray cluster
kubectl apply -f ray-cluster.yaml
```

---

## VCN/LUPINE Integration

### Current State
- VCN-LUPINE is a **separate compute substrate** running on GPU nodes
- NOT managed by k3s (runs as systemd daemons)
- Uses LD_PRELOAD shim to intercept CUDA calls and encode as H.264 video
- Transmits over Tailscale mesh to GPU nodes for actual compute

### Architecture
```
k3s pod (Python/CUDA) → LD_PRELOAD shim → VCN-LUPINE daemon → Tailscale → GPU node → decode → dispatch
```

### Node Assignments
- **qfox-1** (CachyOS, foxtop): Primary compute, runs VCN/LUPINE daemon
- **steamdeck** (NixOS, core): GPU node, runs GPU receiver daemon

### Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 14834 | UDP | VCN-LUPINE frame transmission |
| 8265 | TCP | Ray dashboard (HTTP) |
| 6379 | TCP | Redis (used by Ray) |

### Verification

```bash
# On qfox-1:
systemctl status vcn-lupine-daemon
ss -tulnp | grep 14834

# On steamdeck:
python3 /path/to/vcn_lupine_gpu_node.py --port 14834
systemctl status vcn-lupine-gpu-node
```

### No k3s Changes Required
VCN/LUPINE runs **outside** k3s. No Kubernetes manifests or configuration changes are needed for VCN to work with the new routing stack.

---

## Rollback Scenarios

### Scenario 1: Traefik fails to start on nixos-laptop

**Symptoms:**
- `kubectl get pods -n kube-system` shows Traefik pod crashing
- `journalctl -u k3s` shows errors

**Rollback:**
```bash
ssh root@100.102.173.61 "nixos-rebuild switch --rollback"
# This reverts to agent-only mode with host Caddy doing NodePort routing
```

### Scenario 2: Ingress routing misconfigured

**Symptoms:**
- Internal tests (Phase 4) fail
- 404 or 502 errors for specific paths

**Debug:**
```bash
# Check Ingress resources
kubectl -n services get ingress

# Check Middleware
kubectl -n services get middleware

# Check Traefik logs
kubectl -n kube-system logs -l app=traefik

# Test specific routes
curl -v -H "Host: researchstack.info" http://100.102.173.61:30080/apps/chat/
```

**Fix:** Correct the Ingress/Middleware manifests and reapply:
```bash
kubectl apply -k /etc/nixos/k3s-flake/manifests/
```

### Scenario 3: Public traffic breaks after edge deployment

**Symptoms:**
- Public HTTPS requests return errors
- edge Caddy logs show connection failures to `100.102.173.61:80`

**Debug:**
```bash
# Check edge Caddy
ssh root@100.101.247.127 "journalctl -u caddy -f"

# Check host Caddy on nixos-laptop
ssh root@100.102.173.61 "journalctl -u caddy -f"

# Check Traefik
ssh root@100.102.173.61 "kubectl -n kube-system logs -l app=traefik -f"

# Test chain manually
curl -v http://100.102.173.61:80/  # host Caddy
curl -v http://127.0.0.1:30080/  # Traefik (from nixos-laptop)
```

**Rollback:**
```bash
# Revert edge
ssh root@100.101.247.127 "nixos-rebuild switch --rollback"

# If needed, also revert server
ssh root@100.102.173.61 "nixos-rebuild switch --rollback"
```

---

## Monitoring & Validation

### Playwright Test Suite

The E2E test suite in `tests/` validates:

1. **Edge TLS:** Valid certificates, HTTPS accessibility
2. **Legacy Redirects:** Subdomain 301s work correctly
3. **Path Routing:** `/apps/*`, `/server/*`, `/api/*` routes work
4. **Auth Integration:** forward_auth gates SSO-protected paths
5. **API Bypass:** `/api/*` does NOT redirect to Authentik
6. **Stable Subdomains:** `auth.*`, `mail.*` are preserved

**Run tests:**
```bash
cd tests
npm test                    # All tests
npm run test:edge          # TLS + redirect tests
npm run test:routing       # Path routing tests
npm run test:auth          # Auth integration tests
npx playwright show-report test-results  # View HTML report
```

### Expected Test Results After Full Deployment

| Category | Tests | Expected |
|----------|-------|----------|
| Edge TLS | 5 | All pass |
| Legacy Redirects | 9 | All pass |
| Path Routing | 15 | All pass |
| Auth Integration | 11 | All pass |
| **Total** | **40** | **40 pass** |

---

## Troubleshooting Guide

### Traefik Not Getting NodePort 30080

**Check:**
```bash
kubectl -n kube-system get svc traefik -o yaml | grep nodePort
```

**Fix:**
```bash
# Manual patch
kubectl -n kube-system patch svc traefik --type=json \
  -p '[{"op": "replace", "path": "/spec/ports/0/nodePort", "value": 30080}]'

# Or restart the traefik-nodeport-fix service
systemctl restart traefik-nodeport-fix
```

### Host Caddy Not Forwarding to Traefik

**Check:**
```bash
# Check Caddy config
ssh root@100.102.173.61 "cat /etc/caddy/Caddyfile"

# Check Caddy logs
ssh root@100.102.173.61 "journalctl -u caddy -f"

# Test Caddy directly
curl -v http://100.102.173.61/
```

**Fix:**
```bash
# Restart Caddy
systemctl restart caddy

# Check NixOS config
nixos-rebuild switch --flake .#k3s-server
```

### Ray Dashboard Not Accessible

**Check:**
```bash
# Ray pods running?
kubectl -n ray-system get pods

# Ray service exists?
kubectl -n ray-system get svc raycluster-head-svc

# IngressRoute applied?
kubectl -n ray-system get ingressroute

# Test directly to Ray service
kubectl -n ray-system port-forward svc/raycluster-head-svc 8265:8265
# Then access http://localhost:8265
```

**Fix:**
```bash
# If Ray not deployed, install KubeRay and deploy cluster
kubectl apply -f https://raw.githubusercontent.com/ray-project/kuberay/master/manifests/cluster-scoped-resources.yaml
kubectl apply -f https://raw.githubusercontent.com/ray-project/kuberay/master/manifests/namespaced-resources.yaml
kubectl apply -f ray-cluster.yaml
```

### ForwardAuth Not Working

**Symptoms:** `/apps/*` paths return 200 instead of redirecting to Authentik.

**Check:**
```bash
# ForwardAuth middleware exists?
kubectl -n services get middleware authentik-forward-auth

# Authentik service running?
kubectl -n authentik get pods

# Test forwardAuth URL directly
kubectl -n authentik get svc authentik-server
curl http://authentik-server.authentik.svc.cluster.local:80/outpost.goauthentik.io/auth/traefik
```

**Fix:**
```bash
# Check Ingress annotations
kubectl -n services get ingress rs-apps-chat -o yaml | grep middlewares

# Should include: services-authentik-forward-auth@kubernetescrd
```

---

## Summary of Changes

| File | Change | Purpose |
|------|--------|---------|
| `k3s-server.nix` | Role: agent→server | Enable Traefik |
| `k3s-server.nix` | Add host Caddy | Forward to Traefik |
| `k3s-server.nix` | Add Traefik NodePort fix | Ensure port 30080 |
| `k3s-server.nix` | Add Ray namespace service | Ensure ray-system exists |
| `k3s-server.nix` | Add deploy service | Auto-apply manifests |
| `k3s-server.nix` | Update firewall | Allow Traefik/Ray/VCN ports |
| `manifests/ingress/kustomization.yaml` | Add ray-ingress.yaml | Deploy Ray Ingress |
| `manifests/ingress/middleware.yaml` | Add strip-server-ray | Ray prefix stripping |
| `manifests/ingress/ray-ingress.yaml` | Remove duplicate Middleware | Use shared middleware |

**No changes to k3s-edge.nix** — it already forwards correctly to `100.102.173.61:80`.

---

## Timeline Estimate

| Phase | Duration | Notes |
|-------|----------|-------|
| Phase 0 (prep) | 5 min | Verify current state |
| Phase 1 (k3s-server) | 3 min | NixOS rebuild |
| Phase 2 (verify Traefik) | 2 min | Internal testing |
| Phase 3 (Ingress) | 1 min | Manifests apply |
| Phase 4 (services) | 1 min | Already included |
| Phase 5 (internal test) | 5 min | Validate all paths |
| Phase 6 (k3s-edge) | 2 min | NixOS rebuild |
| Phase 7 (public test) | 5 min | Full validation |
| **Total** | **~24 min** | Budget 30-45 min with troubleshooting |

---

## Success Criteria

✅ All 40 Playwright E2E tests pass  
✅ `https://researchstack.info/` loads (Homer or Authentik redirect)  
✅ `https://auth.researchstack.info/` serves Authentik login  
✅ `https://researchstack.info/server/ray` shows Ray dashboard  
✅ `https://researchstack.info/api/registry/health` returns without redirect  
✅ Legacy subdomain redirects work (status, dash, home, etc.)  
✅ No TLS errors in browser  

---

*Document generated for path-based routing migration. Last updated: 2025-06-01*
