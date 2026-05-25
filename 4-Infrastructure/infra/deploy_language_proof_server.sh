#!/usr/bin/env bash
set -euo pipefail

REMOTE="${REMOTE:-361395-1}"
REMOTE_REPO="${REMOTE_REPO:-/srv/research-stack}"
REMOTE_APP="${REMOTE_APP:-/opt/language-proof-server}"
REMOTE_HOST="${REMOTE_HOST:-100.110.163.82}"
REMOTE_PORT="${REMOTE_PORT:-8787}"
LEAN_ROOT_REL="${LEAN_ROOT_REL:-0-Core-Formalism/lean/Semantics}"
LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCAL_TOKEN_FILE="${LOCAL_TOKEN_FILE:-$HOME/.config/ene/language-proof-server.token}"
ALLOWED_TARGETS="${ALLOWED_TARGETS:-Semantics.FixedPoint,Semantics}"

if [ ! -s "$LOCAL_TOKEN_FILE" ]; then
  install -d -m 700 "$(dirname "$LOCAL_TOKEN_FILE")"
  umask 077
  python3 - <<'PY' >"$LOCAL_TOKEN_FILE"
import secrets
print(secrets.token_urlsafe(48))
PY
fi

ssh "$REMOTE" 'set -euo pipefail
if ! command -v git >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y git
fi
if ! command -v curl >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y curl
fi
if ! command -v rsync >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y rsync
fi
if ! command -v python3 >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y python3
fi
if ! command -v elan >/dev/null 2>&1 && [ ! -x "$HOME/.elan/bin/elan" ]; then
  curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none
fi
if ! id proofsrv >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/language-proof-server --create-home --shell /usr/sbin/nologin proofsrv
fi
mkdir -p /opt/language-proof-server /srv/research-stack /var/lib/language-proof-server/work /var/lib/language-proof-server/receipts /etc/language-proof-server
'

install -m 600 "$LOCAL_TOKEN_FILE" /tmp/language-proof-server.token
scp /tmp/language-proof-server.token "$REMOTE:/etc/language-proof-server/token"
rm -f /tmp/language-proof-server.token

rsync -a --delete \
  --exclude '.git/' \
  --exclude '.lake/build/' \
  --exclude 'lake-packages/*/.git/' \
  --exclude 'lake-packages/*/.lake/' \
  "${LOCAL_ROOT}/4-Infrastructure/infra/language_proof_server.py" \
  "$REMOTE:${REMOTE_APP}/language_proof_server.py"

rsync -a --delete \
  --exclude '.git/' \
  --exclude '.lake/build/' \
  --exclude 'lake-packages/*/.git/' \
  --exclude 'lake-packages/*/.lake/' \
  "${LOCAL_ROOT}/0-Core-Formalism" \
  "${LOCAL_ROOT}/2-Search-Space" \
  "$REMOTE:${REMOTE_REPO}/"

ssh "$REMOTE" "cat >/etc/language-proof-server/proof-server.env" <<ENV
PROOF_SERVER_TOKEN=$(cat "$LOCAL_TOKEN_FILE")
PROOF_ALLOWED_BUILD_TARGETS=${ALLOWED_TARGETS}
ENV

ssh "$REMOTE" "cat >/etc/systemd/system/language-proof-server.service" <<UNIT
[Unit]
Description=Research Stack Language Proof Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=proofsrv
Group=proofsrv
WorkingDirectory=${REMOTE_APP}
EnvironmentFile=/etc/language-proof-server/proof-server.env
Environment=HOME=/var/lib/language-proof-server
Environment=PROOF_SERVER_HOST=${REMOTE_HOST}
Environment=PROOF_SERVER_PORT=${REMOTE_PORT}
Environment=PROOF_REPO_DIR=${REMOTE_REPO}
Environment=PROOF_LEAN_ROOT=${LEAN_ROOT_REL}
Environment=PROOF_WORK_DIR=/var/lib/language-proof-server/work
Environment=PROOF_RECEIPT_DIR=/var/lib/language-proof-server/receipts
ExecStart=/usr/bin/python3 ${REMOTE_APP}/language_proof_server.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/research-stack /var/lib/language-proof-server
CapabilityBoundingSet=
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
UNIT

ssh "$REMOTE" 'set -euo pipefail
chown -R proofsrv:proofsrv /opt/language-proof-server /srv/research-stack /var/lib/language-proof-server
chmod 700 /etc/language-proof-server
chmod 600 /etc/language-proof-server/token /etc/language-proof-server/proof-server.env
if [ ! -x /var/lib/language-proof-server/.elan/bin/elan ]; then
  runuser -u proofsrv -- sh -lc "curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none"
fi
export HOME=/var/lib/language-proof-server
export PATH="$HOME/.elan/bin:$PATH"
cd /srv/research-stack/0-Core-Formalism/lean/Semantics
runuser -u proofsrv -- sh -lc "cd /srv/research-stack/0-Core-Formalism/lean/Semantics && export PATH=/var/lib/language-proof-server/.elan/bin:\$PATH && elan toolchain install \"\$(cat lean-toolchain)\" && lake update"
systemctl daemon-reload
systemctl enable --now language-proof-server.service
systemctl --no-pager --full status language-proof-server.service | sed -n "1,18p"
'

curl -fsS "http://${REMOTE_HOST}:${REMOTE_PORT}/health" | python3 -m json.tool
