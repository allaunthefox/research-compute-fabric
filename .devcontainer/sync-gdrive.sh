#!/usr/bin/env bash
set -euo pipefail

# Portable bidirectional sync for the Research Stack workspace.
# Uses rclone bisync against a Google Drive remote.
#
# Prerequisites (one-time):
#   1. Install rclone: https://rclone.org/install/
#   2. rclone config  →  create a remote named "gdrive"
#      (use Google Drive scope, OAuth via local browser or headless token)
#   3. Create the remote folder / sync root:
#      rclone mkdir gdrive:research-stack
#
# Usage:
#   ./sync-gdrive.sh          # dry-run (preview)
#   ./sync-gdrive.sh --apply  # real sync

REMOTE="gdrive"
REMOTE_PATH="research-stack"
LOCAL_PATH="$(dirname "$(readlink -f "$0")")/.."
SYNC_FLAGS="--create-empty-dirs --compare-size --modify-window=1s --delete --verbose"

if ! command -v rclone &>/dev/null; then
  echo "ERROR: rclone not found. Install from https://rclone.org/install/" >&2
  exit 1
fi

DRY_RUN="--dry-run"
MODE="DRY-RUN (preview)"
if [ "${1:-}" = "--apply" ]; then
  DRY_RUN=""
  MODE="LIVE"
elif [ "${1:-}" = "--resync" ]; then
  # Bisync recovery flag — use when bisync detects a conflict
  DRY_RUN="--resync"
  MODE="RESYNC"
fi

echo "=== Research Stack Sync: $MODE ==="
echo "  Local:  $LOCAL_PATH"
echo "  Remote: $REMOTE:$REMOTE_PATH"
echo ""

rclone bisync "$LOCAL_PATH" "$REMOTE:$REMOTE_PATH" \
  $SYNC_FLAGS \
  $DRY_RUN \
  --exclude '.git/' \
  --exclude '.devcontainer/' \
  --exclude '**/node_modules/' \
  --exclude '**/__pycache__/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '.lake/' \
  --exclude 'lake-packages/' \
  --exclude '.DS_Store' \
  --exclude '*.iso'
