#!/usr/bin/env bash
set -euo pipefail

TOP="cff_accelerator"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="tangnano9k_uart_loopback.cst"
JSON="${TOP}.json"
PNR="${TOP}_pnr.json"
FS="${TOP}.fs"

echo "=== CFF Accelerator Build (Yosys + nextpnr-himbaechel) ==="

RTL_FILES=(
  "${TOP}.v"
  "uart_rx.v"
  "uart_tx.v"
)

echo "=== Synthesis (Yosys) ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat" 2>&1 | tail -20

echo ""
echo "=== Place & Route (nextpnr-himbaechel) ==="
if which nextpnr-himbaechel &>/dev/null; then
  PNR_CMD="nextpnr-himbaechel"
  PNR_CMD="$PNR_CMD --chipdb /usr/share/nextpnr/himbaechel/gowin/chipdb-${FAMILY}.bin"
else
  PNR_CMD="nextpnr-gowin"
fi

$PNR_CMD --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --freq "${FREQ_MHZ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}" 2>&1 | tail -20

echo ""
echo "=== Bitstream (gowin_pack) ==="
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}" 2>&1

echo ""
echo "=== Build complete: ${FS} ==="
echo "To program: sudo openFPGALoader -b tangnano9k -f ${FS}"
