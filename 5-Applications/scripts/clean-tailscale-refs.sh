#!/usr/bin/env bash
set -euo pipefail

# clean-tailscale-refs.sh
# Removes stale Tailscale node references from the repo.
# Run this AFTER clearing the tailnet.

REPO_ROOT="/home/allaun/CascadeProjects/Research-Stack"
cd "$REPO_ROOT"

echo "=========================================="
echo "  Clean Tailscale References"
echo "=========================================="
echo ""

# --- 1. Backup .git/config ---
if [[ -f .git/config ]]; then
    cp .git/config .git/config.backup.$(date +%Y%m%d_%H%M%S)
    echo "[1/6] Backed up .git/config"
fi

# --- 2. Remove Tailscale LFS entries from .git/config ---
# These point to old nodes that no longer exist on the tailnet.
echo "[2/6] Removing Tailscale LFS entries from .git/config..."
git config --local --remove-section 'lfs.https://100.111.192.47/home/judge-gcp-20260330/git-mirrors/research-stack.git/info/lfs' 2>/dev/null || true
git config --local --remove-section 'lfs.https://100.85.1.50/var/git-mirrors/research-stack.git/info/lfs' 2>/dev/null || true
git config --local --remove-section 'lfs.https://100.103.54.58/home/svc-tardy/git-mirrors/research-stack.git/info/lfs' 2>/dev/null || true
git config --local --remove-section 'lfs.http://100.127.111.7:3000/sovereign/research-stack.git/info/lfs' 2>/dev/null || true

# --- 3. Remove i2p aliases from .git/config ---
echo "[3/6] Removing i2p aliases from .git/config..."
git config --local --remove-section 'alias' 2>/dev/null || true

# --- 4. Remove forgejo branch merge-base refs from .git/config ---
echo "[4/6] Removing stale forgejo branch merge-base refs..."
python3 << 'PYEOF'
import re

with open('.git/config', 'r') as f:
    content = f.read()

# Remove any vscode-merge-base line that references forgejo
lines = content.splitlines()
filtered = []
for line in lines:
    if 'vscode-merge-base' in line and 'forgejo' in line:
        continue
    filtered.append(line)

new_content = '\n'.join(filtered) + '\n'

# Also remove forgejo remote section if it exists (it shouldn't, but just in case)
new_content = re.sub(
    r'\[remote "forgejo"\][^\[]*',
    '',
    new_content
)

with open('.git/config', 'w') as f:
    f.write(new_content)
PYEOF

# --- 5. Update .claude/settings.local.json ---
# Remove Bash permissions that reference old tailscale IPs or node names.
echo "[5/6] Cleaning .claude/settings.local.json..."
python3 << 'PYEOF'
import json

with open('.claude/settings.local.json', 'r') as f:
    data = json.load(f)

old_perms = data.get('permissions', {}).get('allow', [])
new_perms = []

skip_patterns = [
    '100.111.192.47',
    '100.110.117.19',
    '100.127.111.7',
    'architect',
    'netcup',
    'judge',
]

for p in old_perms:
    if any(sp in p for sp in skip_patterns):
        continue
    new_perms.append(p)

data['permissions']['allow'] = new_perms

with open('.claude/settings.local.json', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYEOF

# --- 6. Update code files ---
echo "[6/6] Updating code files..."

# 5-Applications/scripts/server.js — comment out architect ping
if [[ -f 5-Applications/scripts/server.js ]]; then
    sed -i 's|exec("ping -c 1 -W 2 100.127.111.7"|// exec("ping -c 1 -W 2 100.127.111.7" // STALE: architect node removed|g' 5-Applications/scripts/server.js 2>/dev/null || true
fi

# 5-Applications/scripts/all_device_signal_topology.py — update qfox reference
if [[ -f 5-Applications/scripts/all_device_signal_topology.py ]]; then
    sed -i 's|"network_node_qfox"|"network_node_primary"|g' 5-Applications/scripts/all_device_signal_topology.py 2>/dev/null || true
    sed -i 's|Network Node (qfox - primary node)|Network Node (Node-00001 - primary node)|g' 5-Applications/scripts/all_device_signal_topology.py 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "Done. Stale references cleaned."
echo ""
echo "Review changes with:"
echo "  git diff .git/config"
echo "  git diff .claude/settings.local.json"
echo "  git diff 5-Applications/scripts/"
echo ""
echo "If satisfied, commit with:"
echo "  git add -A && git commit -m 'chore: remove stale tailscale node references'"
