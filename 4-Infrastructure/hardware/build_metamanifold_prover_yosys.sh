#!/usr/bin/env bash
set -euo pipefail

# Configuration
TOP="MetaManifoldProver"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ_MHZ="27"
CST="metamanifold_prover_gowin.cst"
JSON="metamanifold.json"
FS="metamanifold.fs"

PROJECT_DIR="/home/allaun/Documents/Research Stack/4-Infrastructure/hardware"
cd "$PROJECT_DIR"

echo "=== Meta-Manifold Prover Build (Yosys) ==="
echo "Top: ${TOP}"
echo "Device: ${DEVICE}"
echo "Constraints: ${CST}"

# RTL Files
RTL_FILES=(
  "metamanifold_prover_gowin.v"
)

echo ""
echo "=== Synthesis (Yosys) ==="
yosys -p "read_verilog ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"

echo ""
echo "=== Bitstream (gowin_pack) ==="
# Note: This requires place & route which we don't have a tool for
# gowin_pack expects a placed & routed netlist, not a synthesized JSON
echo "Warning: gowin_pack requires placed & routed netlist"
echo "We need a place & route tool for Gowin FPGAs"
echo ""
echo "Available options:"
echo "1. Install Gowin EDA IDE and use GUI"
echo "2. Fix nextpnr-gowin installation"
echo "3. Use apicula toolchain (if available)"
