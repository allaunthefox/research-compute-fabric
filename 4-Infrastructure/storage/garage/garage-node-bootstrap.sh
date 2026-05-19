#!/usr/bin/env bash
# garage-node-bootstrap.sh
#
# Installs Garage v2.3.0 on a remote Tailscale node, drops a config derived
# from garage.node-template.toml, copies the cluster secret, and enables the
# systemd service. Runs entirely over SSH.
#
# Usage:
#   bash garage-node-bootstrap.sh <tailscale-ip> [ssh-user] [ssh-port]
#
# Prerequisites on the target node:
#   - SSH key access (run: ssh-copy-id -i ~/.ssh/id_ed25519 user@ip)
#   - systemd
#   - curl or wget (for binary download)
#
# After all nodes are bootstrapped, run garage-cluster-init.sh to assign
# layout roles and wire the cluster together.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_IP="${1:?Usage: $0 <tailscale-ip> [user] [port]}"
SSH_USER="${2:-allaun}"
SSH_PORT="${3:-22}"
SSH_KEY="${HOME}/.ssh/id_ed25519"
SSH="ssh -i ${SSH_KEY} -p ${SSH_PORT} -o ConnectTimeout=15 -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

GARAGE_VERSION="v2.3.0"
GARAGE_URL="https://garagehq.deuxfleurs.fr/_releases/${GARAGE_VERSION}/x86_64-unknown-linux-musl/garage"
PRIMARY_NODE_ID="3e08a71b73fa2b1099301844d1f199caab50f7a9209b9929d9bfb2bfeeb937f4"
CLUSTER_SECRET=$(sudo cat /etc/garage/cluster-secret)

log() { echo "[garage-bootstrap] $*" >&2; }

# ── 1. Detect node arch and pick binary ───────────────────────────────────────
log "Probing ${SSH_USER}@${NODE_IP}..."
ARCH=$($SSH "${SSH_USER}@${NODE_IP}" "uname -m" 2>&1)
case "$ARCH" in
    x86_64)  ARCH_TRIPLE="x86_64-unknown-linux-musl" ;;
    aarch64) ARCH_TRIPLE="aarch64-unknown-linux-musl" ;;
    armv6l)  ARCH_TRIPLE="armv6l-unknown-linux-musleabihf" ;;
    *)
        log "ERROR: Unknown arch ${ARCH} — add to case statement"
        exit 1
        ;;
esac
BINARY_URL="https://garagehq.deuxfleurs.fr/_releases/${GARAGE_VERSION}/${ARCH_TRIPLE}/garage"
log "  arch: ${ARCH} → ${ARCH_TRIPLE}"

# ── 2. Probe available data directories ───────────────────────────────────────
DATA_PATH=$($SSH "${SSH_USER}@${NODE_IP}" bash -s << 'REMOTE'
# Find the mount with the most free space that isn't / or tmpfs
df -h --output=target,avail 2>/dev/null \
    | grep -v "^Filesystem\|tmpfs\|devtmpfs\|/boot\|/run\|/sys\|/dev" \
    | sort -k2 -h | tail -1 | awk '{print $1}'
REMOTE
)
# Fall back to / if nothing better found
DATA_PATH="${DATA_PATH:-/}"
log "  data path: ${DATA_PATH}"

META_DIR="${DATA_PATH}/var/lib/garage/meta"
DATA_DIR="${DATA_PATH}/var/lib/garage/data"
[ "$DATA_PATH" = "/" ] && META_DIR="/var/lib/garage/meta" && DATA_DIR="/var/lib/garage/data"

# ── 3. Install on remote ───────────────────────────────────────────────────────
log "Installing Garage ${GARAGE_VERSION} on ${NODE_IP}..."
$SSH "${SSH_USER}@${NODE_IP}" bash -s << REMOTE
set -euo pipefail
# Download binary
curl -sL "${BINARY_URL}" -o /tmp/garage --max-time 120
chmod +x /tmp/garage
sudo mv /tmp/garage /usr/local/bin/garage
garage --version

# Create directories and user
sudo useradd -r -s /bin/false -d /var/lib/garage garage 2>/dev/null || true
sudo mkdir -p "${META_DIR}" "${DATA_DIR}" /etc/garage /var/log/garage
sudo chown -R garage:garage /var/lib/garage /etc/garage /var/log/garage 2>/dev/null || true
echo "Garage installed"
REMOTE

# ── 4. Copy cluster secret ────────────────────────────────────────────────────
log "Copying cluster secret..."
echo "${CLUSTER_SECRET}" | $SSH "${SSH_USER}@${NODE_IP}" \
    "sudo tee /etc/garage/cluster-secret > /dev/null && sudo chmod 600 /etc/garage/cluster-secret"

# ── 5. Generate admin token and drop config ───────────────────────────────────
NODE_ADMIN_TOKEN=$(openssl rand -hex 32)
CONFIG=$(sed \
    -e "s|NODE_TAILSCALE_IP|${NODE_IP}|g" \
    -e "s|META_DIR|${META_DIR}|g" \
    -e "s|DATA_DIR|${DATA_DIR}|g" \
    -e "s|PRIMARY_NODE_ID|${PRIMARY_NODE_ID}|g" \
    "${SCRIPT_DIR}/garage.node-template.toml")

echo "${CONFIG}" | $SSH "${SSH_USER}@${NODE_IP}" \
    "sudo tee /etc/garage/garage.toml > /dev/null"
echo "GARAGE_ADMIN_TOKEN=${NODE_ADMIN_TOKEN}" | $SSH "${SSH_USER}@${NODE_IP}" \
    "sudo tee /etc/garage/garage.env > /dev/null && sudo chmod 600 /etc/garage/garage.env"

# ── 6. Install and start systemd service ──────────────────────────────────────
log "Installing systemd service on ${NODE_IP}..."
cat "${SCRIPT_DIR}/garage.service" | $SSH "${SSH_USER}@${NODE_IP}" \
    "sudo tee /etc/systemd/system/garage.service > /dev/null"

$SSH "${SSH_USER}@${NODE_IP}" bash -s << 'REMOTE'
sudo systemctl daemon-reload
sudo systemctl enable garage
sudo systemctl start garage
sleep 2
sudo systemctl status garage --no-pager | head -8
REMOTE

# ── 7. Get node ID and print connect command ───────────────────────────────────
log "Fetching node ID..."
sleep 2
NODE_ID=$($SSH "${SSH_USER}@${NODE_IP}" \
    "sudo garage -c /etc/garage/garage.toml --admin-token ${NODE_ADMIN_TOKEN} node id 2>/dev/null | head -1")

log ""
log "Bootstrap complete for ${NODE_IP}."
log "Node ID: ${NODE_ID}"
log ""
log "To connect this node to the cluster, run on qfox-1:"
log "  sudo garage -c /etc/garage/garage.toml node connect ${NODE_ID}"
log ""
log "Then run: bash garage-cluster-init.sh  (after all nodes are bootstrapped)"

# Append to node registry
python3 - << PYEOF
import json, os
from datetime import datetime, timezone

registry_path = "${SCRIPT_DIR}/../node-registry.json"
entry = {
    "hostname": "${NODE_IP}",
    "tailscale_ip": "${NODE_IP}",
    "ssh_user": "${SSH_USER}",
    "ssh_port": ${SSH_PORT},
    "garage_node_id": "${NODE_ID}",
    "garage_data_dir": "${DATA_DIR}",
    "added_at": datetime.now(timezone.utc).isoformat()
}

registry = []
if os.path.exists(registry_path):
    with open(registry_path) as f:
        try:
            registry = json.load(f)
        except Exception:
            registry = []

registry = [r for r in registry if r.get("tailscale_ip") != entry["tailscale_ip"]]
registry.append(entry)
with open(registry_path, "w") as f:
    json.dump(registry, f, indent=2)
print(f"Registered {entry['tailscale_ip']} in node-registry.json")
PYEOF
