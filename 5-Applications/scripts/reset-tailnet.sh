#!/usr/bin/env bash
set -euo pipefail

# reset-tailnet.sh
# Clears all Tailscale nodes and re-authenticates current node as Node-00001

CURRENT_HOSTNAME=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('Self',{}).get('HostName','unknown'))")
TAILNET=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('MagicDNSSuffix','unknown'))")

echo "=========================================="
echo "  Tailnet Reset Tool"
echo "=========================================="
echo "Current node:  $CURRENT_HOSTNAME"
echo "Tailnet:       $TAILNET"
echo ""

# Step 1: Logout current node
echo "[1/2] Logging out current node ($CURRENT_HOSTNAME)..."
sudo tailscale logout
echo "Done. Node removed from tailnet."
echo ""

# Step 2: Re-auth as Node-00001
echo "[2/2] Re-authenticating as Node-00001..."
echo "You will see an auth URL. Open it in your browser to complete login."
echo ""
sudo tailscale up --hostname=Node-00001 --ssh --accept-routes

echo ""
echo "=========================================="
echo "Current node re-authenticated as Node-00001"
echo ""
tailscale status
echo ""
echo "=========================================="
echo "NEXT STEPS: Remove remaining nodes"
echo "=========================================="
echo ""
echo "The other 9 nodes must be removed via the Tailscale admin console"
echo "or API since they are not reachable from this machine."
echo ""
echo "Option A: Manual removal (recommended)"
echo "  1. Go to: https://login.tailscale.com/admin/machines"
echo "  2. Select each old node and click 'Remove...'"
echo "  3. Old nodes: architect, desktop-0u2ceal, foxtop, ip-172-31-25-81,"
echo "     judge, laptop-1, netcup-router, racknerd-510bd9c, racknerd-atl"
echo ""
echo "Option B: API removal (batch)"
echo "  1. Get an API key: https://login.tailscale.com/admin/settings/keys"
echo "  2. Run: ./scripts/remove-tailnet-nodes-api.sh <YOUR_API_KEY>"
echo ""
echo "Option C: SSH into active nodes and logout"
echo "  ssh judge 'sudo tailscale logout'"
echo "  ssh netcup-router 'sudo tailscale logout'"
echo "  ssh ip-172-31-25-81 'sudo tailscale logout'"
echo ""
echo "After clearing all nodes, run: ./scripts/clean-tailscale-refs.sh"
echo "to remove stale Tailscale references from this repo."
