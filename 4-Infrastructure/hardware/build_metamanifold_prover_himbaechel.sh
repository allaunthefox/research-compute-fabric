#!/usr/bin/env bash
set -euo pipefail

# Configuration
TOP="MetaManifoldProver"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="metamanifold_prover_test.cst"
JSON="metamanifold.json"
PNR="metamanifold_pnr.json"
FS="metamanifold.fs"

PROJECT_DIR="/home/allaun/Documents/Research Stack/4-Infrastructure/hardware"
cd "$PROJECT_DIR"

echo "=== Meta-Manifold Prover Build (Yosys + nextpnr-himbaechel) ==="
echo "Top: ${TOP}"
echo "Device: ${DEVICE}"
echo "Constraints: ${CST}"

# RTL Files
RTL_FILES=(
  "metamanifold_prover_test.v"
)

echo ""
echo "=== Synthesis (Yosys) ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"

echo ""
echo "=== Place & Route (nextpnr-himbaechel) ==="
nextpnr-himbaechel --device "${DEVICE}" --json "${JSON}" --write "${PNR}" --freq "${FREQ_MHZ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}" --chipdb /usr/share/nextpnr/himbaechel/gowin/chipdb-GW1N-9C.bin

echo ""
echo "=== Bitstream (gowin_pack) ==="
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}"

echo ""
echo "=== Build complete: ${FS} ==="
echo ""
echo "To program the FPGA:"
echo "  openFPGALoader -b tangnano9k -f ${FS}"
