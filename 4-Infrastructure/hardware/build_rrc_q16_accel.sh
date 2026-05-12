#!/usr/bin/env bash
set -euo pipefail

TOP="tangnano9k_rrc_q16_accel"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="tangnano9k_uart_loopback.cst"
JSON="${TOP}.json"
PNR="${TOP}_pnr.json"
FS="${TOP}.fs"
CHIPDB="${CHIPDB:-/usr/share/nextpnr/himbaechel/gowin/chipdb-${FAMILY}.bin}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_NEXTPNR="${SCRIPT_DIR}/../bin/nextpnr-himbaechel"

RTL_FILES=(
  "${TOP}.v"
  "uart_rx.v"
  "uart_tx.v"
)

cd "${SCRIPT_DIR}"

echo "=== Tang Nano 9K Rainbow Raccoon Q16 Accelerator Build ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"

if [ -x "${REPO_NEXTPNR}" ]; then
  PNR_CMD="${REPO_NEXTPNR}"
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
sha256sum "${FS}"
echo "=== Build complete: ${SCRIPT_DIR}/${FS} ==="
