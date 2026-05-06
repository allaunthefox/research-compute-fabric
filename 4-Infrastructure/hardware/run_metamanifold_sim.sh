#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="/tmp/verilator_metamanifold_sim"
SRC_DIR="${BUILD_DIR}/src"
TOP="MetaManifoldProver"

clean() {
    rm -rf "$BUILD_DIR"
}

build() {
    mkdir -p "$SRC_DIR"
    # Copy sources to a no-space path for Verilator's internal Make
    cp "${SCRIPT_DIR}/metamanifold_prover_gowin.v" "$SRC_DIR/${TOP}.v"
    cp "${SCRIPT_DIR}/metamanifold_prover_tb.cpp" "$SRC_DIR/tb_${TOP}.cpp"

    cd "$BUILD_DIR"
    verilator -Wall -Wpedantic -Wno-fatal \
        -cc --exe --build --trace \
        -Mdir "$BUILD_DIR" \
        --top-module "$TOP" \
        "${SRC_DIR}/${TOP}.v" \
        "${SRC_DIR}/tb_${TOP}.cpp"
}

run() {
    local trace_flag="${TRACE:-0}"
    if [[ "$trace_flag" == "1" ]]; then
        TRACE=1 "$BUILD_DIR/V${TOP}"
    else
        "$BUILD_DIR/V${TOP}"
    fi
}

case "${1:-all}" in
    clean)
        clean
        ;;
    build)
        build
        ;;
    run)
        run
        ;;
    trace)
        TRACE=1 run
        ;;
    all)
        clean
        build
        run
        ;;
    *)
        echo "Usage: $0 {clean|build|run|trace|all}"
        exit 1
        ;;
esac
