#!/usr/bin/env bash
# PipeWire capture → chunked FLAC → S3C GPU manifold bridge
# Full pipeline: pw-record → PCM → s3c-tool (GPU/CPU) → JSON receipts
# Set PW_TARGET env to override auto-detected audio source
set -euo pipefail

FLAC="${FLAC:-flac}"
S3C_TOOL="${S3C_TOOL:-s3c-tool}"
OUTDIR="${OUTDIR:-/tmp/pw-dsp}"
mkdir -p "$OUTDIR"

# Auto-detect first available audio input source
if [ -z "${PW_TARGET:-}" ]; then
  PW_TARGET=$(pactl list sources short 2>/dev/null | grep -v monitor | awk '{print $2}' | head -1 || true)
  if [ -z "$PW_TARGET" ]; then
    echo "[pw-dsp] WARNING: no audio input source found, trying default"
    PW_TARGET="0"
  fi
fi

echo "[pw-dsp] S3C GPU manifold bridge starting (target=$PW_TARGET)"

while true; do
  TS=$(date -u +%Y%m%dT%H%M%SZ)
  RAW="$OUTDIR/raw_$TS.s16le"
  FLAC_FILE="$OUTDIR/chunk_$TS.flac"
  RECEIPT="$OUTDIR/receipt_$TS.json"

  # Capture 2-second PCM chunk via PipeWire (raw s16le, 48kHz mono)
  pw-record --latency=100ms --target="$PW_TARGET" --rate=48000 --channels=1 --format=s16 "$RAW" &
  PW_PID=$!
  sleep 2
  kill "$PW_PID" 2>/dev/null || true
  wait "$PW_PID" 2>/dev/null || true

  if [ ! -s "$RAW" ]; then continue; fi

  # Compress to FLAC (lossless, ~57% compression on noise floor)
  $FLAC --best --no-padding --stdout --endian=little --sign=signed --channels=1 --bps=16 --sample-rate=48000 "$RAW" 2>/dev/null > "$FLAC_FILE"

  # Process through GPU-accelerated S3C manifold
  $S3C_TOOL --aggregate < "$RAW" 2>/dev/null > "$RECEIPT" || true

  RAW_SIZE=$(stat -c%s "$RAW" 2>/dev/null || echo 0)
  FLAC_SIZE=$(stat -c%s "$FLAC_FILE" 2>/dev/null || echo 0)

  if [ -s "$RECEIPT" ]; then
    EMISSION=$(python3 -c "import json; d=json.load(open('$RECEIPT')); print(d['results'][0]['stats']['emission_ratio'])" 2>/dev/null || echo "?")
    J_AVG=$(python3 -c "import json; d=json.load(open('$RECEIPT')); print(d['results'][0]['stats']['avg_j'])" 2>/dev/null || echo "?")
    echo "[pw-dsp] $TS: ${RAW_SIZE}B raw, ${FLAC_SIZE}B FLAC, emission=$EMISSION, avg_j=$J_AVG"
  else
    echo "[pw-dsp] $TS: ${RAW_SIZE}B raw, ${FLAC_SIZE}B FLAC (no receipt)"
  fi

  # Keep FLAC chunk, remove raw PCM
  rm -f "$RAW"
done
