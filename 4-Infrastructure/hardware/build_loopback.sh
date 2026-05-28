#!/usr/bin/env bash
set -euo pipefail

# Configuration
TOP="tangnano9k_uart_loopback"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="${CST:-tangnano9k_uart_loopback.cst}"
JSON="tangnano9k_uart_loopback.json"
PNR="tangnano9k_uart_loopback_pnr.json"
FS="tangnano9k_uart_loopback.fs"

# Path to tools
ROOT=".."
NEXTPNR="${ROOT}/tools/build/nextpnr-himbaechel/nextpnr-himbaechel"


echo "=== Tang Nano 9K UART Loopback Build ==="
echo "Top: ${TOP}"
echo "Device: ${DEVICE}"
echo "Constraints: ${CST}"

# RTL Files
RTL_FILES=(
  "tangnano9k_uart_loopback.v"
  "uart_rx.v"
  "uart_tx.v"
)

echo ""
echo "=== Synthesis (Yosys) ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"

echo ""
echo "=== Place & Route (nextpnr) ==="
# Try local nextpnr first, then fallback to environment
if [ -x "${NEXTPNR}" ]; then
  PNR_CMD="${NEXTPNR}"
else
  PNR_CMD="nextpnr-himbaechel"
fi

"${PNR_CMD}" --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --freq "${FREQ_MHZ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}"

echo ""
echo "=== Bitstream (gowin_pack) ==="
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}"

echo ""
echo "=== Build complete: ${FS} ==="
