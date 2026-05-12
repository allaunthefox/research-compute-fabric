#!/usr/bin/env bash
set -euo pipefail

TOP="tangnano9k_hutter_symbol_surface"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="tangnano9k_uart_loopback.cst"
JSON="tangnano9k_hutter_symbol_surface.json"
PNR="tangnano9k_hutter_symbol_surface_pnr.json"
FS="tangnano9k_hutter_symbol_surface.fs"
CHIPDB="${CHIPDB:-/usr/share/nextpnr/himbaechel/gowin/chipdb-${FAMILY}.bin}"

ROOT=".."
NEXTPNR="${ROOT}/tools/build/nextpnr-himbaechel/nextpnr-himbaechel"

RTL_FILES=(
  "tangnano9k_hutter_symbol_surface.v"
  "hutter_symbol_substitution_core.v"
  "pbacs_1bit_transport_core.v"
  "uart_rx.v"
  "uart_tx.v"
)

echo "=== Tang Nano 9K Hutter Symbol Surface Build ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"

if [ -x "${NEXTPNR}" ]; then
  PNR_CMD="${NEXTPNR}"
else
  PNR_CMD="nextpnr-himbaechel"
fi

PNR_ARGS=(
  --device "${DEVICE}"
  --json "${JSON}"
  --write "${PNR}"
  --freq "${FREQ_MHZ}"
  --vopt "family=${FAMILY}"
  --vopt "cst=${CST}"
)

if [ -f "${CHIPDB}" ]; then
  PNR_ARGS+=(--chipdb "${CHIPDB}")
fi

"${PNR_CMD}" "${PNR_ARGS[@]}"

gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}"
echo "=== Build complete: ${FS} ==="
