#!/usr/bin/env bash
set -e
JF="http://100.85.244.73:30810"

echo "=== Step 1: Create admin user ==="
curl -s -X POST "$JF/Startup/User" \
  -H "Content-Type: application/json" \
  -d '{"Name":"allaun","Password":"9oP63nz4JRvdRO"}'
echo ""

echo "=== Step 2: Mark wizard complete ==="
curl -s -X POST "$JF/Startup/Complete"
echo ""

echo "=== Step 3: Login ==="
LOGIN=$(curl -s "$JF/Users/AuthenticateByName" \
  -H "Content-Type: application/json" \
  -d '{"Username":"allaun","Pw":"9oP63nz4JRvdRO"}')
TOKEN=$(echo "$LOGIN" | grep -o '"AccessToken":"[^"]*"' | cut -d'"' -f4)
echo "Token: ${TOKEN:0:20}..."

if [ -n "$TOKEN" ]; then
  echo "=== Step 4: List plugins ==="
  curl -s "$JF/Plugins" -H "Authorization: MediaBrowser Token=$TOKEN" | grep -o '"Name":"[^"]*"' | head -10
  
  echo "=== Step 5: Find OpenID plugin ==="
  PLUGINS=$(curl -s "$JF/Plugins" -H "Authorization: MediaBrowser Token=$TOKEN")
  echo "$PLUGINS" | grep -i "openid\|oidc" | head -5
  
  echo "=== Step 6: Install OpenID plugin ==="
  PLUGIN_ID=$(echo "$PLUGINS" | python3 -c "import sys,json;d=json.load(sys.stdin);[print(p['Id']) for p in d if 'OpenID' in p['Name']]" 2>/dev/null)
  if [ -n "$PLUGIN_ID" ]; then
    echo "Installing plugin: $PLUGIN_ID"
    curl -s -X POST "$JF/Plugins/$PLUGIN_ID/Install" -H "Authorization: MediaBrowser Token=$TOKEN"
    echo "Plugin installed. Restart required."
  else
    echo "Plugin not found in catalog"
  fi
fi
