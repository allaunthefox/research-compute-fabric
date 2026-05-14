#!/usr/bin/env bash
#
# run_qc_flag.sh — Shell wrapper for lean_qc_flagger.py
#
# Usage:
#   ./run_qc_flag.sh <target> [options]
#
# Wraps the Python QC flagger, always produces JSON + Markdown in a dated
# output directory, and prints a summary to stdout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLAGGER="${SCRIPT_DIR}/lean_qc_flagger.py"

if [ ! -f "$FLAGGER" ]; then
    echo "ERROR: lean_qc_flagger.py not found at $FLAGGER" >&2
    exit 1
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 <target> [--verbose]" >&2
    echo "  target: Lean file or directory to scan" >&2
    exit 1
fi

TARGET="$1"
VERBOSE=""
if [ "${2:-}" = "--verbose" ] || [ "${2:-}" = "-v" ]; then
    VERBOSE="--verbose"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTDIR="${SCRIPT_DIR}/reports/${TIMESTAMP}"
mkdir -p "$OUTDIR"

JSON_OUT="${OUTDIR}/qc_flags.json"
MD_OUT="${OUTDIR}/qc_flags.md"

echo "────────────────────────────────────────────"
echo " QC Flag Scan"
echo " Target:    ${TARGET}"
echo " Reports:   ${OUTDIR}/"
echo "────────────────────────────────────────────"

python3 "$FLAGGER" "$TARGET" --json "$JSON_OUT" --markdown "$MD_OUT" $VERBOSE

echo ""
echo "────────────────────────────────────────────"
echo " Reports saved to ${OUTDIR}/"
echo "  JSON:  ${JSON_OUT}"
echo "  MD:    ${MD_OUT}"
echo "────────────────────────────────────────────"
