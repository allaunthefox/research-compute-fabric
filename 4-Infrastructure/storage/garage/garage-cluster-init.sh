#!/usr/bin/env bash
# garage-cluster-init.sh
#
# Run after all nodes have been bootstrapped with garage-node-bootstrap.sh.
# This script:
#   1. Connects all nodes to the cluster (garage node connect)
#   2. Assigns layout roles (zone + capacity) to each node
#   3. Bumps replication_factor to 3 once 3+ nodes are available
#   4. Verifies bucket and key state
#
# Usage:
#   bash garage-cluster-init.sh
#
# Idempotent — safe to re-run.

set -euo pipefail

ADMIN_TOKEN=$(sudo grep GARAGE_ADMIN_TOKEN /etc/garage/garage.env | cut -d= -f2)
G="sudo garage -c /etc/garage/garage.toml --admin-token ${ADMIN_TOKEN}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${SCRIPT_DIR}/../node-registry.json"

log() { echo "[cluster-init] $*" >&2; }

log "Current cluster status:"
$G status 2>&1
echo ""

# ── 1. Connect all registered nodes ───────────────────────────────────────────
if [ -f "$REGISTRY" ]; then
    log "Connecting nodes from registry..."
    python3 - << PYEOF
import json, subprocess, sys

with open("${REGISTRY}") as f:
    nodes = json.load(f)

for node in nodes:
    node_id = node.get("garage_node_id", "").strip()
    ip = node.get("tailscale_ip", "")
    if not node_id or "@" not in node_id:
        # node_id should be full_id@ip:port format
        if node_id:
            node_id = f"{node_id}@{ip}:3901"
        else:
            print(f"  SKIP {ip}: no garage_node_id recorded yet")
            continue
    print(f"  Connecting: {node_id[:16]}...@{ip}:3901")
    result = subprocess.run(
        ["sudo", "garage", "-c", "/etc/garage/garage.toml",
         "--admin-token", "${ADMIN_TOKEN}",
         "node", "connect", node_id],
        capture_output=True, text=True
    )
    if result.returncode == 0 or "already" in result.stdout.lower():
        print(f"    OK")
    else:
        print(f"    WARN: {result.stderr.strip()[:80]}")
PYEOF
fi

sleep 2
log "Cluster after connect:"
$G status 2>&1
echo ""

# ── 2. Count healthy nodes ─────────────────────────────────────────────────────
HEALTHY_NODES=$($G status 2>&1 | grep -c "v2\." || echo 0)
log "Healthy nodes: ${HEALTHY_NODES}"

# ── 3. Assign layout roles ─────────────────────────────────────────────────────
log "Assigning layout roles..."
$G layout show 2>&1

# Assign each unroled node a zone based on its tag
# Zone strategy: group local nodes together, VPS (microvm-racknerd) in its own zone
# This ensures Garage spreads replicas across failure domains.
LAYOUT_VERSION=$($G layout show 2>&1 | grep "^Current cluster layout version" | awk '{print $NF}' || echo 1)
NEXT_VERSION=$((LAYOUT_VERSION + 1))

$G status 2>&1 | grep "NO ROLE ASSIGNED" | awk '{print $1}' | while read node_id; do
    HOSTNAME=$($G status 2>&1 | grep "$node_id" | awk '{print $2}')
    # Assign zone: VPS nodes get zone=vps, local Tailscale nodes get zone=local
    if echo "$HOSTNAME $node_id" | grep -qi "microvm\|racknerd\|vps"; then
        ZONE="vps"
    else
        ZONE="local"
    fi
    log "  Assigning $node_id ($HOSTNAME) → zone=$ZONE, 200G"
    $G layout assign "$node_id" --zone "$ZONE" --capacity 200G 2>&1 || true
done

# ── 4. Bump replication factor if enough nodes ────────────────────────────────
if [ "$HEALTHY_NODES" -ge 3 ]; then
    log "3+ nodes available — bumping replication_factor to 3"
    sudo sed -i 's/replication_factor = 1/replication_factor = 3/' /etc/garage/garage.toml
    # Remove old layout so it can be recreated with rf=3
    sudo systemctl stop garage
    sudo rm -f /var/lib/garage/meta/cluster_layout
    sudo systemctl start garage
    sleep 3
    # Re-assign all roles
    log "Re-assigning all layout roles for rf=3..."
    $G status 2>&1 | grep "NO ROLE ASSIGNED" | awk '{print $1}' | while read node_id; do
        $G layout assign "$node_id" --zone local --capacity 200G 2>&1 || true
    done
    # Assign primary separately
    $G layout assign 3e08a71b73fa2b10 --zone local --capacity 900G --tag primary 2>&1 || true
    NEXT_VERSION=1
fi

# ── 5. Apply layout ────────────────────────────────────────────────────────────
log "Applying layout (version ${NEXT_VERSION})..."
$G layout apply --version "${NEXT_VERSION}" 2>&1

sleep 2

# ── 6. Verify buckets and keys ─────────────────────────────────────────────────
log "Verifying buckets..."
EXISTING=$($G bucket list 2>&1)
for bucket in research-stack db-scratch rds-overflow snap-zone gdrive-mirror; do
    if echo "$EXISTING" | grep -q "$bucket"; then
        echo "  OK  $bucket"
    else
        $G bucket create "$bucket" 2>&1
        echo "  CREATED  $bucket"
    fi
done

KEY_ID="GK55105d55675994caea2c2d3d"
for bucket in research-stack db-scratch rds-overflow snap-zone gdrive-mirror; do
    $G bucket allow --read --write --owner "$bucket" --key "$KEY_ID" 2>&1 | grep -v "^==" || true
done

log ""
log "Final cluster status:"
$G status 2>&1
$G bucket list 2>&1
