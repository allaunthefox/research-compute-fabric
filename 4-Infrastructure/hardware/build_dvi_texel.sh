#!/usr/bin/env bash
set -euo pipefail

TOP="dvi_texel_transmitter"
DEVICE="GW1NR-LV9QN88PC6/I5"
FAMILY="GW1N-9C"
CST="tangnano9k_dvi.cst"

# Constraint file for DVI texel transmitter
cat > "$CST" << 'CSTEOF'
// Tang Nano 9K DVI Texel Transmitter constraints
// HDMI connector pin mappings for GW1NR-LV9QN88PC6/I5

IO_LOC "clk_27mhz" 52;
IO_PORT "clk_27mhz" IO_TYPE=LVCMOS33 PULL_MODE=NONE;

IO_LOC "rst_n" 4;
IO_PORT "rst_n" IO_TYPE=LVCMOS33 PULL_MODE=UP;

// DVI/HDMI output pins (TMDS-compatible, 3.3V LVCMOS output)
// Tang Nano 9K HDMI connector uses direct FPGA pin routing
// DVI_R[7:0]
IO_LOC "dvi_r[7]" 30; IO_PORT "dvi_r[7]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[6]" 31; IO_PORT "dvi_r[6]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[5]" 34; IO_PORT "dvi_r[5]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[4]" 35; IO_PORT "dvi_r[4]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[3]" 36; IO_PORT "dvi_r[3]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[2]" 37; IO_PORT "dvi_r[2]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[1]" 38; IO_PORT "dvi_r[1]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_r[0]" 39; IO_PORT "dvi_r[0]" IO_TYPE=LVCMOS33 DRIVE=8;

// DVI_G[7:0]
IO_LOC "dvi_g[7]" 41; IO_PORT "dvi_g[7]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[6]" 42; IO_PORT "dvi_g[6]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[5]" 43; IO_PORT "dvi_g[5]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[4]" 44; IO_PORT "dvi_g[4]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[3]" 45; IO_PORT "dvi_g[3]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[2]" 46; IO_PORT "dvi_g[2]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[1]" 56; IO_PORT "dvi_g[1]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_g[0]" 57; IO_PORT "dvi_g[0]" IO_TYPE=LVCMOS33 DRIVE=8;

// DVI_B[7:0]
IO_LOC "dvi_b[7]" 58; IO_PORT "dvi_b[7]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[6]" 60; IO_PORT "dvi_b[6]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[5]" 61; IO_PORT "dvi_b[5]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[4]" 62; IO_PORT "dvi_b[4]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[3]" 63; IO_PORT "dvi_b[3]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[2]" 64; IO_PORT "dvi_b[2]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[1]" 65; IO_PORT "dvi_b[1]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_b[0]" 66; IO_PORT "dvi_b[0]" IO_TYPE=LVCMOS33 DRIVE=8;

// DVI sync and clock
IO_LOC "dvi_hsync" 67; IO_PORT "dvi_hsync" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_vsync" 68; IO_PORT "dvi_vsync" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_de"    69; IO_PORT "dvi_de" IO_TYPE=LVCMOS33 DRIVE=8;
IO_LOC "dvi_clk"   70; IO_PORT "dvi_clk" IO_TYPE=LVCMOS33 DRIVE=8;

// LEDs
IO_LOC "led[0]" 10; IO_LOC "led[1]" 11; IO_LOC "led[2]" 13;
IO_LOC "led[3]" 14; IO_LOC "led[4]" 15; IO_LOC "led[5]" 16;
IO_PORT "led[0]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "led[1]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "led[2]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "led[3]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "led[4]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "led[5]" IO_TYPE=LVCMOS33 DRIVE=8;
CSTEOF

JSON="${TOP}.json"
PNR="${TOP}_pnr.json"
FS="${TOP}.fs"

echo "=== DVI Texel Transmitter Build ==="
echo "Synth: ${TOP}.v"

yosys -p "read_verilog ${TOP}.v; synth_gowin -top ${TOP} -json ${JSON}; stat" 2>&1 | tail -15

echo "Place & Route..."
nextpnr-himbaechel --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --vopt "family=${FAMILY}" --vopt "cst=${CST}" \
  --chipdb /usr/share/nextpnr/himbaechel/gowin/chipdb-${FAMILY}.bin 2>&1 | tail -10

echo "Bitstream..."
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}" 2>&1

echo "=== ${FS} ==="
ls -lh "${FS}"
