#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

TOP="research_stack_top"
CST="research_stack_tangnano9k.cst"
JSON="research_stack_top.json"
PNR="research_stack_top_pnr.json"
FS="research_stack_top.fs"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
FREQ=27

Q16_V="../../5-Applications/out/verilog/q16_lut_core.v"

echo "=== Synthesis ==="
yosys -p "
  read_verilog -sv \
    ${Q16_V} \
    blitter_memory_map.v \
    voltage_mode_controller.v \
    scale_space_bram.v \
    highs_pivot_accelerator.v \
    fractal_box_counter.v \
    fractal_fd_selector.v \
    spatial_hash_bram.v \
    spatial_hash_selector.v \
    Blitter6502OISC_small.v \
    research_stack_top.v;
  synth_gowin -top ${TOP} -json ${JSON};
  stat
"

echo ""
echo "=== Place & Route ==="
nextpnr-himbaechel --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --freq "${FREQ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}"

echo ""
echo "=== Bitstream ==="
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}"

echo ""
echo "=== Done: ${FS} ==="
ls -lh "${FS}"
