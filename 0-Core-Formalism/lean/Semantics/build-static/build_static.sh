#!/usr/bin/env bash
# OTOM Static Compilation Suite
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEMANTICS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SEMANTICS_DIR}/../../.." && pwd)"

LEAN_CC="${LEAN_CC:-gcc}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"
VERBOSE="${VERBOSE:-0}"
LTO="${LTO:-0}"
TARGET_DIR="${TARGET_DIR:-${SEMANTICS_DIR}/build-static/out}"
BUILD_TYPE="${BUILD_TYPE:-static}"

EXECUTABLES=(bindserver searchserver SemanticsCli openworm_benchmark \
    ExtremeParameterTestEval NominalParameterTestEval moim_benchmark \
    generate_sparkle_phi_s3c tangnano9k_emitter)

log() { echo "[build_static] $*"; }
usage() {
    cat <<'EOF'
Usage: ./build_static.sh [target] [options]
Targets: all release check lint verilog synthesis clean docker
Options: --cc <c> --jobs <n> --verbose --lto --target-dir <d> --help
EOF
}

check() {
    log "Verifying toolchain..."
    command -v "$LEAN_CC" >/dev/null || { log "ERROR: compiler not found"; exit 1; }
    command -v lake >/dev/null || { log "ERROR: lake not found"; exit 1; }
    command -v lean >/dev/null || { log "ERROR: lean not found"; exit 1; }
    echo "  Compiler: $(${LEAN_CC} --version | head -1)"
    echo "  Lake: $(lake --version | head -1)"
    echo "  Lean: $(lean --version)"
}

flags() {
    local f="-static -static-libgcc"
    case "$BUILD_TYPE" in
        static) f="$f -O2" ;;
        release) f="$f -O3 -ffunction-sections -fdata-sections"
            [[ "$LTO" == 1 ]] && f="$f -flto -fwhole-program" && log "LTO enabled"
            ;;
        debug) f="$f -O0 -g" ;;
    esac
    echo "$f"
}

build_all() {
    local f="$(flags)"
    log "Building ($BUILD_TYPE): $f"
    mkdir -p "$TARGET_DIR"
    cd "$SEMANTICS_DIR"
    export LEAN_CC LEANC_OPTS="$f ${LEANC_OPTS:-}"
    [[ "$VERBOSE" == 1 ]] && echo "LEAN_CC=$LEAN_CC LEANC_OPTS=$LEANC_OPTS"
    lake build
    for exe in "${EXECUTABLES[@]}"; do
        log "Building: $exe"
        lake build "$exe"
    done
    local bin_dir="$SEMANTICS_DIR/.lake/build/bin"
    for exe in "${EXECUTABLES[@]}"; do
        local p="$bin_dir/$exe"
        [[ -f "$p" ]] || { log "WARNING: $exe not found"; continue; }
        if command -v ldd >/dev/null; then
            if ldd "$p" 2>&1 | grep -qE 'not a dynamic|statically linked'; then
                log "OK: $exe is static"
            else
                local n=$(ldd "$p" 2>/dev/null | grep -c '^\s*lib' || echo 0)
                [[ "$n" == 0 ]] && log "OK: $exe (no dynamic deps)" || log "WARN: $exe has $n dynamic deps"
            fi
        fi
        cp "$p" "$TARGET_DIR/"
    done
    log "Done. Binaries in: $TARGET_DIR"
}

lint() { cd "$SEMANTICS_DIR" && ./scripts/zero_trust_linter.sh; }
verilog() { cd "$SEMANTICS_DIR" && lake exe tangnano9k_emitter && lake exe generate_sparkle_phi_s3c; }
synthesis() { verilog; "$PROJECT_ROOT/5-Applications/out/verilog/build_tangnano9k.sh"; }
clean() { cd "$SEMANTICS_DIR" && lake clean 2>/dev/null || true; rm -rf "$TARGET_DIR"; log "Cleaned"; }

docker_build() {
    docker build -t otom-lean-static -f "$SCRIPT_DIR/Dockerfile.static" "$PROJECT_ROOT"
    docker run --rm -v "$PROJECT_ROOT:/workspace" -e BUILD_DIR=/workspace/build-static/out \
        otom-lean-static bash -c 'cd /workspace/0-Core-Formalism/lean/Semantics/build-static && ./build_static.sh all'
}

# Parse args
TARGET="all"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cc) LEAN_CC="$2"; shift 2 ;;
        --jobs) JOBS="$2"; shift 2 ;;
        --verbose) VERBOSE=1; shift ;;
        --lto) LTO=1; shift ;;
        --target-dir) TARGET_DIR="$2"; shift 2 ;;
        --help) usage; exit 0 ;;
        -*) echo "Unknown: $1"; usage; exit 1 ;;
        *) TARGET="$1"; shift ;;
    esac
done

case "$TARGET" in
    all|static) check && build_all ;;
    release) BUILD_TYPE=release; check && build_all ;;
    debug) BUILD_TYPE=debug; check && build_all ;;
    check) check ;;
    lint) lint ;;
    verilog) check && verilog ;;
    synthesis) check && synthesis ;;
    clean) clean ;;
    docker) docker_build ;;
    *) echo "Unknown target: $TARGET"; usage; exit 1 ;;
esac
