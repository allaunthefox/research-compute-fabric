# Disaster Recovery — Research Stack

**Last updated:** 2026-05-29

Procedures for backing up and restoring all Research Stack components.

---

## k3s Cluster

### Backup etcd

```bash
# Snapshot etcd (on control plane node — nixos)
sudo k3s etcd-snapshot save \
  --name researchstack-backup \
  --dir /var/lib/rancher/k3s/server/db/snapshots

# List snapshots
sudo ls -la /var/lib/rancher/k3s/server/db/snapshots/

# Copy snapshot off-node
scp /var/lib/rancher/k3s/server/db/snapshots/researchstack-backup-* \
  user@backup-host:/backups/k3s/
```

### Restore from Snapshot

```bash
# On control plane (nixos):
sudo systemctl stop k3s

# Restore
sudo k3s server \
  --cluster-reset \
  --cluster-reset-restore-path=/var/lib/rancher/k3s/server/db/snapshots/researchstack-backup-<timestamp>

# Restart
sudo systemctl start k3s

# Verify
export KUBECONFIG=/tmp/researchstack-kubeconfig.yaml
kubectl get nodes
kubectl get pods -A
```

### Backup Manifests

All Kubernetes manifests are in the git repo. The source of truth is:

```bash
cd ~/Research\ Stack
git push origin main
```

### Automated Backup Schedule

Create a cron job on nixos:

```bash
# /etc/cron.d/k3s-backup
0 3 * * * root k3s etcd-snapshot save --name researchstack-backup --dir /var/lib/rancher/k3s/server/db/snapshots && \
  find /var/lib/rancher/k3s/server/db/snapshots/ -mtime +7 -delete
```

---

## FPGA — Tang Nano 9K

### Backup Bitstream

The bitstream source and compiled output are in the git repo:

```bash
cd ~/Research\ Stack

# Source
ls 4-Infrastructure/hardware/*.v

# Compiled bitstream
ls 4-Infrastructure/hardware/research_stack_top.fs
```

### Re-flash from Git

```bash
cd ~/Research\ Stack

# Rebuild if needed
cd 4-Infrastructure/hardware && bash build_research_stack.sh

# Flash
openFPGALoader -b tangnano9k research_stack_top.fs

# Verify
openFPGALoader -b tangnano9k --verify research_stack_top.fs
```

### Backup SRAM Contents

SRAM contents are volatile (lost on power cycle). To preserve runtime state:

```python
# Dump memory via UART before power-off
import serial, struct

ser = serial.Serial('/dev/ttyUSB0', 115384, timeout=10)

# Trigger memory dump (send HALT with dump flag)
# ... protocol-specific ...

# Read and save
with open('fpga_memory_dump.bin', 'wb') as f:
    data = ser.read(8192)  # 4K words = 8K bytes
    f.write(data)

ser.close()
```

---

## Tailscale

### Re-authenticate Node

```bash
# On the node that lost auth:
sudo systemctl restart tailscaled
tailscale up --authkey=<TS_AUTH_KEY>

# Or interactive
tailscale up
```

### Re-join Tailnet

```bash
# Check current status
tailscale status

# If node is missing from tailnet:
# 1. Generate new auth key at https://login.tailscale.com/admin/settings/keys
# 2. On the node:
sudo tailscale up --authkey=tskey-auth-<key>

# Verify connectivity
tailscale ping nixos-laptop
tailscale ping qfox-1
```

### Backup Tailscale State

Tailscale state is stored at `/var/lib/tailscale/`:

```bash
# Backup state directory
sudo tar czf /backups/tailscale-state-$(date +%Y%m%d).tar.gz \
  /var/lib/tailscale/

# Restore
sudo systemctl stop tailscaled
sudo tar xzf /backups/tailscale-state-*.tar.gz -C /
sudo systemctl start tailscaled
```

---

## Git Repository

### Backup

The canonical backup is the remote origin. Ensure all changes are pushed:

```bash
cd ~/Research\ Stack

# Check for unpushed commits
git log --oneline origin/main..HEAD

# Push everything
git push origin main --tags

# Verify clean state
git status --branch --short --untracked-files=all
```

### Restore from Remote

```bash
# Clone fresh
cd ~
git clone <remote-url> "Research Stack"

# Or reset to remote state
cd ~/Research\ Stack
git fetch origin
git reset --hard origin/main
```

### Backup Remotes

```bash
# List remotes
cd ~/Research\ Stack
git remote -v

# Add backup remote
git remote add backup <backup-url>
git push backup main --tags
```

---

## Secrets (sops-nix / age)

### Backup age Keys

```bash
# age key location (NixOS)
cat /etc/age/keys.txt

# Backup
cp /etc/age/keys.txt /backups/age-keys-$(date +%Y%m%d).txt
chmod 600 /backups/age-keys-*.txt

# Or from home directory
cat ~/.config/sops/age/keys.txt
```

### Restore age Keys

```bash
# Restore key file
cp /backups/age-keys-*.txt /etc/age/keys.txt
chmod 600 /etc/age/keys.txt

# Verify sops can decrypt
sops -d secrets.enc.yaml
```

### Backup sops Configuration

```bash
# The .sops.yaml config is in the repo
cat ~/Research\ Stack/.sops.yaml

# Encrypted secrets are also in the repo
find ~/Research\ Stack -name '*.enc.yaml' -o -name '*.enc.json'
```

### Regenerate age Key (Last Resort)

```bash
# Generate new key pair
age-keygen -o /etc/age/keys.txt

# Get public key
age-keygen -y /etc/age/keys.txt

# Re-encrypt all secrets with new key
# (requires old key or plaintext backup)
sops updatekeys secrets.enc.yaml
```

---

## DNS — Porkbun

### Backup API Key

```bash
# From k8s secret
kubectl get secret porkbun-credentials -n services \
  -o jsonpath='{.data.api-key}' | base64 -d

# Back up securely
echo "<api-key>" | age -r <backup-age-pubkey> > /backups/porkbun-api.age

# Or store in password manager
```

### Recover API Key

1. Log in to [Porkbun](https://porkbun.com)
2. Navigate to **Account → API Access**
3. Regenerate or copy existing API key
4. Update k8s secret:

```bash
kubectl create secret generic porkbun-credentials \
  -n services \
  --from-literal=api-key=<new-key> \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart Caddy to pick up new key
kubectl rollout restart deployment/caddy -n services
```

### Verify DNS Records

```bash
dig researchstack.info +short
dig auth.researchstack.info +short
dig registry.researchstack.info +short

# Test Porkbun API
curl -X POST https://api.porkbun.com/api/json/v3/ping \
  -H "Content-Type: application/json" \
  -d '{"apikey": "<key>", "secretapikey": "<secret>"}'
```

---

## Recovery Priority Order

When restoring from a total failure, follow this order:

| Step | Component | Depends On |
|------|-----------|------------|
| 1 | **Tailscale** | Auth key (from password manager or backup) |
| 2 | **Git repo** | Network connectivity (Tailscale or direct) |
| 3 | **age keys** | Backup location |
| 4 | **k3s cluster** | etcd snapshot + age keys for secrets |
| 5 | **DNS/Porkbun** | API key (from backup or Porkbun account) |
| 6 | **FPGA** | Git repo (source + bitstream) |
| 7 | **Services** | k3s cluster + secrets + DNS |

---

## Full System Checklist

After recovery, verify each component:

- [ ] Tailscale: `tailscale status` shows all 5 nodes
- [ ] k3s: `kubectl get nodes` shows all nodes Ready
- [ ] Pods: `kubectl get pods -A` — all Running/Succeeded
- [ ] DNS: `dig researchstack.info` resolves correctly
- [ ] TLS: cert valid (`openssl s_client`)
- [ ] Auth: `auth.researchstack.info` loads Authentik
- [ ] Funnel: `361395-1.tail4e7094.ts.net` responds
- [ ] Ollama: `curl http://100.88.57.96:31434/api/tags` returns models
- [ ] FPGA: `openFPGALoader --detect` sees Tang Nano 9K
- [ ] Dashboard: `https://researchstack.info` shows Homer
