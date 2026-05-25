#!/usr/bin/env bash
set -e

# Create unit file
cat > /etc/systemd/system/rs-credential-server.service << 'UNITEOF'
[Unit]
Description=Research Stack Credential Server
After=network-online.target tailscaled.service
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
Environment=RS_CREDENTIAL_SERVER=http://100.101.247.127:8444
Environment=RS_SURFACE_NODE_ID=aws-nixos-node-1
# RDS credential for ENE session sync — set via SOPS secret or env file
# Environment=CREDENTIAL_RDS_DSN=postgresql://user:pass@host:5432/db

[Install]
WantedBy=multi-user.target
UNITEOF

systemctl daemon-reload
systemctl enable rs-credential-server
systemctl restart rs-credential-server

echo "Service status:"
systemctl status rs-credential-server --no-pager --lines=5
echo ""
echo "Testing health endpoint..."
curl -sf --connect-timeout 5 http://localhost:8444/health && echo "OK" || echo "FAIL"

# Test remote credential resolution
echo ""
echo "Testing remote credential resolution..."
curl -sf --connect-timeout 10 http://localhost:8444/credentials/deepseek | python3 -m json.tool
