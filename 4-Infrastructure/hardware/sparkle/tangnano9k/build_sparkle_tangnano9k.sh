#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ROOT="../../.."
TOP="${SPARKLE_TOP:-SparkleTangNano9KTop}"
DEVICE="${SPARKLE_DEVICE:-GW1NR-LV9QN88PC6/I5}"
FAMILY="${SPARKLE_FAMILY:-GW1N-9C}"
FREQ_MHZ="${SPARKLE_FREQ_MHZ:-27}"
CST="${SPARKLE_CST:-sparkle_tangnano9k.cst}"
JSON="${SPARKLE_JSON:-sparkle_tangnano9k.json}"
PNR="${SPARKLE_PNR:-sparkle_tangnano9k_pnr.json}"
FS="${SPARKLE_FS:-sparkle_tangnano9k.fs}"
LOCAL_NEXTPNR="${ROOT}/tools/build/nextpnr-himbaechel/nextpnr-himbaechel"
if [[ -n "${SPARKLE_NEXTPNR:-}" ]]; then
  NEXTPNR="${SPARKLE_NEXTPNR}"
elif [[ -x "${LOCAL_NEXTPNR}" ]]; then
  NEXTPNR="${LOCAL_NEXTPNR}"
else
  NEXTPNR="${ROOT}/tools/bin/nextpnr-himbaechel"
fi
GENERATOR="${SPARKLE_GENERATOR:-generate_sparkle_phi_s3c}"
BOARD="${SPARKLE_BOARD:-tangnano9k}"
SYNTH_ONLY=0
FLASH_SRAM=0

# Default payload: Sparkle-generated Phi/S3C hardware seed.
DEFAULT_RTL=(
  "SparkleTangNano9KTop.v"
  "../generated/sparkle_phi_s3c_payload.sv"
)

if [[ -n "${SPARKLE_RTL:-}" ]]; then
  # shellcheck disable=SC2206
  RTL_FILES=(${SPARKLE_RTL})
else
  RTL_FILES=("${DEFAULT_RTL[@]}")
fi

usage() {
  cat <<'USAGE'
Usage: ./build_sparkle_tangnano9k.sh [--check] [--synth-only] [--flash-sram]

Options:
  --check       Print the active target and verify required tools.
  --synth-only  Stop after Sparkle dependency build and Yosys synthesis.
  --flash-sram  Load the generated bitstream into FPGA SRAM after build.
USAGE
}

check_nextpnr_runtime() {
  test -x "${NEXTPNR}"
  if command -v ldd >/dev/null; then
    if ldd "${NEXTPNR}" | grep -q "not found"; then
      echo "nextpnr runtime dependencies are missing:" >&2
      ldd "${NEXTPNR}" | grep "not found" >&2
      return 1
    fi
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      CHECK_ONLY=1
      ;;
    --synth-only)
      SYNTH_ONLY=1
      ;;
    --flash-sram)
      FLASH_SRAM=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "${CHECK_ONLY:-0}" == "1" ]]; then
  echo "target=${TOP}"
  echo "device=${DEVICE}"
  echo "family=${FAMILY}"
  echo "freq_mhz=${FREQ_MHZ}"
  echo "constraints=${CST}"
  printf 'rtl=%s\n' "${RTL_FILES[@]}"
  command -v yosys >/dev/null
  command -v gowin_pack >/dev/null
  check_nextpnr_runtime
  exit 0
fi

echo "=== Sparkle Tang Nano 9K target ==="
echo "top: ${TOP}"
echo "device: ${DEVICE}"
echo "family: ${FAMILY}"
echo "freq MHz: ${FREQ_MHZ}"
echo "constraints: ${CST}"

echo ""
echo "=== Generate Sparkle Phi/S3C payload ==="
(cd "${ROOT}/tools/lean/Semantics" && lake exe "${GENERATOR}")

echo ""
echo "=== Synthesis ==="
yosys -p "read_verilog -sv ${RTL_FILES[*]}; synth_gowin -top ${TOP} -json ${JSON}; stat"

if [[ "${SYNTH_ONLY}" == "1" ]]; then
  echo ""
  echo "=== Synth-only complete: ${JSON} ==="
  exit 0
fi

echo ""
echo "=== Place & Route ==="
check_nextpnr_runtime
"${NEXTPNR}" --device "${DEVICE}" --json "${JSON}" --write "${PNR}" \
  --freq "${FREQ_MHZ}" --vopt "family=${FAMILY}" --vopt "cst=${CST}"

echo ""
echo "=== Bitstream ==="
gowin_pack -d "${FAMILY}" -o "${FS}" "${PNR}"

echo ""
echo "=== Build complete: ${FS} ==="

if [[ "${FLASH_SRAM}" == "1" ]]; then
  echo ""
  echo "=== Flash SRAM (${BOARD}) ==="
  command -v openFPGALoader >/dev/null
  openFPGALoader -b "${BOARD}" "${FS}"
fi
