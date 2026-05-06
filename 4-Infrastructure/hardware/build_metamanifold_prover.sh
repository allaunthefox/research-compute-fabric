#!/bin/bash
# Build script for Meta-Manifold Prover on Gowin GW1NR-9 / Tang Nano 9K

set -e

PROJECT_DIR="/home/allaun/Documents/Research Stack/4-Infrastructure/hardware"
VERILOG_FILE="$PROJECT_DIR/metamanifold_prover_gowin.v"
CST_FILE="$PROJECT_DIR/metamanifold_prover_gowin.cst"
OUTPUT_DIR="$PROJECT_DIR/build_metamanifold"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Building Meta-Manifold Prover for Gowin GW1NR-9..."

# Gowin synthesis command
GOWIN_SH="/usr/bin/gw_sh"

if [ ! -f "$GOWIN_SH" ]; then
    echo "Error: Gowin EDA tools not found at $GOWIN_SH"
    echo "Please install Gowin EDA tools or update the path in this script"
    exit 1
fi

# Create project file
cat > "$OUTPUT_DIR/metamanifold.gprj" << EOF
{
    "file_name": "metamanifold",
    "design": {
        "device": "GW1NR-9",
        "package": "LQFP48",
        "performance": "C8/I6"
    },
    "files": [
        {
            "name": "$VERILOG_FILE",
            "file_type": "verilog"
        }
    ],
    "constraint": {
        "file_name": "$CST_FILE"
    }
}
EOF

# Run synthesis
echo "Running synthesis..."
cd "$OUTPUT_DIR"
$GOWIN_SH << EOF
create_project -name metamanifold -device GW1NR-9 -package LQFP48 -proj_dir $OUTPUT_DIR
add_file -verilog $VERILOG_FILE
add_file -constraint $CST_FILE
set_option -synthesis_effort high
synth
place
route
bitstream -output $OUTPUT_DIR/metamanifold.fs
EOF

echo "Build complete!"
echo "Bitstream: $OUTPUT_DIR/metamanifold.fs"
echo ""
echo "To program the FPGA:"
echo "  openFPGALoader -b tangnano9k -f $OUTPUT_DIR/metamanifold.fs"
