#!/usr/bin/env bash
set -e
JF="http://100.85.244.73:30810"
TOKEN="a83a07226c384a4e8230c951a8461f38"

echo "=== Step 1: Add SSO plugin repository ==="
# Check existing repositories
REPOS=$(curl -s "$JF/Plugins/Repository" -H "Authorization: MediaBrowser Token=$TOKEN" 2>/dev/null)
echo "Existing repos: $REPOS"

# Add the SSO plugin repository
curl -s -X POST "$JF/Plugins/Repository" \
  -H "Authorization: MediaBrowser Token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Name":"Jellyfin SSO","Url":"https://raw.githubusercontent.com/9p4/jellyfin-plugin-sso/manifest-release/manifest.json"}' 2>&1

echo ""
echo "=== Step 2: List available plugins ==="
# Get plugins from the marketplace
MARKET=$(curl -s "$JF/Plugins/Marketplace" -H "Authorization: MediaBrowser Token=$TOKEN" 2>&1)
echo "Marketplace response: ${MARKET:0:100}"

echo ""
echo "=== Step 3: Install SSO plugin ==="
PLUGINS=$(curl -s "$JF/Plugins" -H "Authorization: MediaBrowser Token=$TOKEN")
echo "$PLUGINS" | /nix/store/6spx8g41ccb6y762wzz73zmvzs449b2v-python3-3.12.8-env/bin/python3 -c "
import sys,json
d=json.load(sys.stdin)
for p in d:
    if 'sso' in p['Name'].lower() or 'auth' in p['Name'].lower():
        print(f\"Installed: {p['Name']} ({p['Id']})\")"
