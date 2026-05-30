#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Fractal Box Counter — standalone build for Tang Nano 9K
# Verifies synthesis, P&R, and bitstream generation for the
# fractal dimension computation modules.

TOP="fractal_box_counter"
CST="research_stack_tangnano9k.cst"
JSON="fractal_box_counter.json"
PNR="fractal_box_counter_pnr.json"
FS="fractal_box_counter.fs"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ=27

echo "=== Fractal Box Counter Build ==="
echo "Top:     ${TOP}"
echo "Device:  ${DEVICE}"
echo "CST:     ${CST}"
echo ""

# ── Step 1: Synthesis ─────────────────────────────────────────────
echo "=== Step 1: Synthesis (Yosys) ==="
yosys -p "
  read_verilog -sv \
    fractal_box_counter.v \
    fractal_fd_selector.v;
  synth_gowin -top ${TOP} -json ${JSON};
  stat
"

# ── Step 2: Place & Route ─────────────────────────────────────────
echo ""
echo "=== Step 2: Place & Route (nextpnr-himbaechel) ==="
nextpnr-himbaechel --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --freq "${FREQ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}"

# ── Step 3: Bitstream ─────────────────────────────────────────────
echo ""
echo "=== Step 3: Bitstream (gowin_pack) ==="
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}"

# ── Step 4: Resource Report ───────────────────────────────────────
echo ""
echo "=== Step 4: Resource Usage Report ==="
if [ -f "${JSON}" ]; then
    echo "Synthesis JSON: ${JSON}"
    # Extract cell counts from yosys stat output (already printed above)
fi
if [ -f "${PNR}" ]; then
    echo "P&R JSON:       ${PNR}"
fi
if [ -f "${FS}" ]; then
    FS_SIZE=$(stat -c%s "${FS}" 2>/dev/null || stat -f%z "${FS}" 2>/dev/null || echo "unknown")
    echo "Bitstream:      ${FS} (${FS_SIZE} bytes)"
else
    echo "WARNING: Bitstream not generated!"
fi

echo ""
echo "=== Build complete: ${FS} ==="
ls -lh "${FS}" 2>/dev/null || true
