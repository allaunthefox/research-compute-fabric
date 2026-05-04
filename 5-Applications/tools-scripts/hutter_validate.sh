#!/bin/bash
# HUTTER PRIZE: MINIMAL VALIDATION PATH
# Strictly follows the bytes -> cells -> signatures -> patches pipeline.

set -e

SHARD="data/enwik8_huggingface/context128-stride1/test-00000-of-00002.parquet"
ANALYZER="data/hutter_test/hutter_test_bundle/analyze_enwik8_cells.py"
PYTHON="./hutter_venv/bin/python3"

echo "=========================================="
echo "HUTTER MINIMAL VALIDATION"
echo "=========================================="

# 1. Check dependencies
if [ ! -f "$PYTHON" ]; then
    echo "[!] Creating tight virtual environment..."
    python3 -m venv hutter_venv
    ./hutter_venv/bin/pip install pyarrow -q
fi

# 2. Check shard
if [ ! -f "$SHARD" ]; then
    echo "[!] Shard missing. Attempting LFS pull..."
    cd data/enwik8_huggingface && git lfs pull --include "context128-stride1/test-00000-of-00002.parquet" && cd ../..
fi

# 3. Run Analysis
echo "[*] Extracting 1000 windows from $SHARD..."
RESULT=$($PYTHON "$ANALYZER" "$SHARD" --limit 1000)

# 4. Sanity Metrics
CELLS_TOTAL=$(echo "$RESULT" | jq '.cells_total')
WINDOWS=$(echo "$RESULT" | jq '.windows_analyzed')
DISTINCT_CELLS=$(echo "$RESULT" | jq '.distinct_exact_cells')
ADMISSIBLE=$(echo "$RESULT" | jq '.admissible_patch_ratio')
WITNESS=$(echo "$RESULT" | jq -r '.lean_witness')

CELLS_PER_WINDOW=$((CELLS_TOTAL / WINDOWS))

echo ""
echo "--- Results ---"
echo "Cells Per Window : $CELLS_PER_WINDOW (Target: 64)"
echo "Distinct Cells   : $DISTINCT_CELLS (Target: << $CELLS_TOTAL)"
echo "Admissible Ratio : $ADMISSIBLE (Target: ~1.0)"
echo "Lean Witness     : $WITNESS"

# 5. Lawful Exit
if [ "$CELLS_PER_WINDOW" -eq 64 ] && [ "$WITNESS" == "lawful_hutter_compression" ]; then
    echo ""
    echo "✅ VALIDATION PASSED: Real benchmark-shaped signal confirmed."
    exit 0
else
    echo ""
    echo "❌ VALIDATION FAILED: Signal is synthetic or artifacts detected."
    exit 1
fi
