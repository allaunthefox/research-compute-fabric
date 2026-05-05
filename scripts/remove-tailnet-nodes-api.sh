#!/usr/bin/env bash
set -euo pipefail

# remove-tailnet-nodes-api.sh
# Batch-removes all old Tailscale nodes via API.
# Usage: ./scripts/remove-tailnet-nodes-api.sh <TS_API_KEY>

API_KEY="${1:-}"
if [[ -z "$API_KEY" ]]; then
    echo "Usage: $0 <TS_API_KEY>"
    echo "Get your API key at: https://login.tailscale.com/admin/settings/keys"
    exit 1
fi

TAILNET=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('MagicDNSSuffix','unknown'))")
if [[ "$TAILNET" == "unknown" ]]; then
    echo "Could not determine tailnet. Are you logged into Tailscale?"
    exit 1
fi

# Nodes to remove (all except Node-00001 which is the current re-authed node)
OLD_NODES=(
    "architect"
    "desktop-0u2ceal"
    "foxtop"
    "ip-172-31-25-81"
    "judge"
    "laptop-1"
    "netcup-router"
    "racknerd-510bd9c"
    "racknerd-atl"
    "qfox"
    "QFox"
)

echo "Tailnet: $TAILNET"
echo "Removing old nodes via API..."
echo ""

# Fetch all devices
DEVICES_JSON=$(curl -sS \
    -H "Authorization: Bearer $API_KEY" \
    "https://api.tailscale.com/api/v2/tailnet/-/devices")

# Extract device IDs for old nodes
for node in "${OLD_NODES[@]}"; do
    DEVICE_ID=$(echo "$DEVICES_JSON" | python3 -c "
import sys, json
devices = json.load(sys.stdin).get('devices', [])
for d in devices:
    if d.get('name', '').split('.')[0] == '$node':
        print(d.get('id'))
        break
")
    if [[ -n "$DEVICE_ID" ]]; then
        echo "Removing $node (ID: $DEVICE_ID)..."
        HTTP_STATUS=$(curl -sS -o /dev/null -w "%{http_code}" \
            -X DELETE \
            -H "Authorization: Bearer $API_KEY" \
            "https://api.tailscale.com/api/v2/device/$DEVICE_ID")
        if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "204" ]]; then
            echo "  OK (HTTP $HTTP_STATUS)"
        else
            echo "  FAILED (HTTP $HTTP_STATUS)"
        fi
    else
        echo "$node: not found (already removed?)"
    fi
done

echo ""
echo "Done. Verify at: https://login.tailscale.com/admin/machines"
