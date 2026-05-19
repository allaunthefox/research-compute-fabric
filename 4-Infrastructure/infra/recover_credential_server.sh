#!/usr/bin/env bash
# Deploy credential server to microVM (RackNerd)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VM_IP="172.245.19.182"
VM_USER="root"
VM_PASS="${1:-}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

if [ -z "$VM_PASS" ]; then
    VM_PASS="$(cat "$REPO_ROOT/API KEYS/racknerd_510bd9c_root.txt" 2>/dev/null | grep root_password | cut -d: -f2 | tr -d ' ')"
fi

if [ -z "$VM_PASS" ]; then
    echo "ERROR: root password required. Pass as argument or ensure API KEYS/racknerd_510bd9c_root.txt exists."
    exit 1
fi

SSH="sshpass -p "$VM_PASS" ssh $SSH_OPTS ${VM_USER}@${VM_IP}"
SCP="sshpass -p "$VM_PASS" scp $SSH_OPTS"

echo "=== Deploying credential server to ${VM_IP} ==="

# Create directories
$SSH "mkdir -p /opt/rs-surface /etc/rs-surface"

# Upload rs-surface binary (credential endpoint is served by rs-surface on /credentials)
RS_SURFACE_BIN="$REPO_ROOT/4-Infrastructure/infra/embedded_surface/rs-surface/target/x86_64-unknown-linux-musl/release/rs-surface"
if [ ! -x "$RS_SURFACE_BIN" ]; then
  echo "ERROR: rs-surface binary not found at $RS_SURFACE_BIN — build it first with:"
  echo "  cd $REPO_ROOT/4-Infrastructure/infra/embedded_surface/rs-surface && cargo build --release --target x86_64-unknown-linux-musl"
  exit 1
fi
echo "Uploading rs-surface binary..."
$SCP "$RS_SURFACE_BIN" ${VM_USER}@${VM_IP}:/opt/rs-surface/rs-surface

# Copy credentials config
CRED_JSON="/tmp/rs-credentials.json"
python3 -c "
import json, os
creds = {}
for var, key in [('DEEPSEEK_API_KEY', 'deepseek'), ('QUANDELA_API_KEY', 'quandela'),
                  ('WOLFRAM_ALPHA_APPID', 'wolfram_alpha'), ('LINEAR_API_KEY', 'linear'),
                  ('AWS_BEARER_TOKEN_BEDROCK', 'bedrock')]:
    val = os.environ.get(var, '')
    if val:
        creds[key] = val
if not creds:
    print('WARNING: no credential env vars set; writing empty config')
with open('$CRED_JSON', 'w') as f:
    json.dump(creds, f, indent=2)
print(f'Wrote {len(creds)} provider keys from environment')
"
echo "Uploading credentials.json..."
$SCP "$CRED_JSON" ${VM_USER}@${VM_IP}:/etc/rs-surface/credentials.json
rm -f "$CRED_JSON"

# Create systemd service
echo "Setting up systemd service..."
$SSH 'cat > /etc/systemd/system/rs-credential-server.service << '"'"'SERVICEEOF'"'"'
[Unit]
Description=Research Stack Credential Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rs-surface
ExecStart=/opt/rs-surface/rs-surface
Restart=always
RestartSec=5
Environment=RS_CREDENTIAL_CONFIG=/etc/rs-surface/credentials.json
Environment=RS_SURFACE_PORT=8444
Environment=RS_SURFACE_HOST=0.0.0.0

[Install]
WantedBy=multi-user.target
SERVICEEOF'

# Stop old service if exists, enable new one
$SSH "systemctl daemon-reload && systemctl enable rs-credential-server && systemctl restart rs-credential-server"

# Verify
echo "=== Verifying ==="
sleep 2
$SSH "systemctl status rs-credential-server --no-pager --lines=5"
echo ""
echo "=== Testing HTTP ==="
curl -sf --connect-timeout 5 http://${VM_IP}:8444/ && echo "" || echo "(curl root)"
curl -sf --connect-timeout 5 http://${VM_IP}:8444/health && echo "" || echo "(curl health)"
curl -sf --connect-timeout 5 http://${VM_IP}:8444/status && echo "" || echo "(curl status)"
curl -sf --connect-timeout 5 http://${VM_IP}:8444/openapi.json | python3 -m json.tool > /dev/null 2>&1 && echo "openapi.json: valid" || echo "openapi.json: FAIL"

echo "=== Deploy complete ==="
echo "API: http://${VM_IP}:8444/"
echo "Docs: http://${VM_IP}:8444/openapi.json"
echo "Credentials: http://${VM_IP}:8444/credentials"
