#!/usr/bin/env bash
set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$WORKDIR/out/logs"
mkdir -p "$LOGDIR"

TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
{
  echo "=== RUN $TS ==="
  echo "--- benchmark_bitcoin_local.py ---"
  "$WORKDIR/.venv/bin/python3" "$WORKDIR/scripts/benchmark_bitcoin_local.py" --simulate-regtest || echo "benchmark failed"
  echo "--- balance_watcher.py ---"
  "$WORKDIR/.venv/bin/python3" "$WORKDIR/scripts/balance_watcher.py" --datadir "$WORKDIR/out/bitcoind_regtest" --threshold-usd 1000 --once || echo "balance_watcher failed"
  echo "=== DONE $TS ==="
} >> "$LOGDIR/scheduler.log" 2>&1

exit 0
