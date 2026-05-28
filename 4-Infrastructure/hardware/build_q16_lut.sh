#!/usr/bin/env bash
set -euo pipefail

# Configuration
TOP="q16_lut_top"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="tangnano9k_q16_lut.cst"
JSON="q16_lut_top.json"
PNR="q16_lut_top_pnr.json"
FS="q16_lut_top.fs"

# Path to tools (local build or environment)
ROOT=".."
NEXTPNR="${ROOT}/tools/build/nextpnr-himbaechel/nextpnr-himbaechel"

# Verilog source directory
VERILOG_DIR="../../5-Applications/out/verilog"

echo "=== Tang Nano 9K Q16 LUT Core Build ==="
echo "Top: ${TOP}"
echo "Device: ${DEVICE}"
echo "Constraints: ${CST}"
echo ""

# RTL Files
RTL_FILES=(
  "${VERILOG_DIR}/q16_lut_core.v"
  "q16_lut_top.v"
)

# Step 1: Synthesis with Yosys
echo "=== Step 1: Synthesis (Yosys) ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"
echo ""

# Step 2: Place & Route with nextpnr
echo "=== Step 2: Place & Route (nextpnr) ==="
if [ -x "${NEXTPNR}" ]; then
  PNR_CMD="${NEXTPNR}"
else
  PNR_CMD="nextpnr-himbaechel"
fi

"${PNR_CMD}" --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --freq "${FREQ_MHZ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}"
echo ""

# Step 3: Pack bitstream
echo "=== Step 3: Bitstream (gowin_pack) ==="
gowin_pack -d "GW1N-9C" -o "${FS}" "${PNR}"
echo ""

# Step 4: Report resource usage
echo "=== Step 4: Resource Report ==="
if [ -f "${FS}" ]; then
  FS_SIZE=$(stat -c%s "${FS}" 2>/dev/null || stat -f%z "${FS}" 2>/dev/null)
  echo "Bitstream file: ${FS}"
  echo "Bitstream size: ${FS_SIZE} bytes"
else
  echo "WARNING: Bitstream file not found!"
fi
echo ""
echo "=== Build complete: ${FS} ==="
