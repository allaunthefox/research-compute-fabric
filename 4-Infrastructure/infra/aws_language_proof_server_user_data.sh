#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl git python3 rsync zstd ca-certificates

if ! id proofsrv >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/language-proof-server --create-home --shell /usr/sbin/nologin proofsrv
fi

install -d -m 755 /opt/language-proof-server
install -d -m 755 /srv/research-stack
install -d -m 700 -o proofsrv -g proofsrv /var/lib/language-proof-server
install -d -m 700 -o proofsrv -g proofsrv /var/lib/language-proof-server/work
install -d -m 700 -o proofsrv -g proofsrv /var/lib/language-proof-server/receipts
install -d -m 700 /etc/language-proof-server

cat >/etc/motd <<'MOTD'
Research Stack language proof server.
Dedicated Lean/Lake proof-check node. Do not co-locate general services here.
MOTD
