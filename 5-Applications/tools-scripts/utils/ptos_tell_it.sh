#!/usr/bin/env bash
# ptos_tell_it.sh
# Usage: ./scripts/ptos_tell_it.sh <sources_file> [limit]
# Requirements: OMNITOKEN env var set, scripts/omnitoken_soliton_ping.py and scripts/build_ptos_metadata_db.py exist.

set -euo pipefail

SOURCES=${1:-/tmp/omni_sources.txt}
LIMIT=${2:-50}

if [ -z "${OMNITOKEN-}" ]; then
  echo "Error: OMNITOKEN environment variable is not set." >&2
  exit 1
fi

if [ ! -f "$SOURCES" ]; then
  echo "Error: sources file not found: $SOURCES" >&2
  exit 1
fi

echo "[PTOS-TELL-IT] Starting Omnitoken soliton ping with sources=$SOURCES limit=$LIMIT"
python3 scripts/omnitoken_soliton_ping.py --sources "$SOURCES" --limit "$LIMIT"

echo "[PTOS-TELL-IT] Rebuilding PTOS metadata DB"
python3 scripts/build_ptos_metadata_db.py

echo "[PTOS-TELL-IT] Summary"
sqlite3 ptos_metadata.db "SELECT COUNT(*) AS entries FROM metadata_entries;"
sqlite3 ptos_metadata.db "SELECT COUNT(*) AS connections FROM connections;"

cat <<'EOF'
DONE: PTOS pipeline complete.
  - Check omnitoken_adaptive_state.json
  - Check omnitoken_pattern_pool.json
  - Check ptos_metadata_graph.json
EOF
