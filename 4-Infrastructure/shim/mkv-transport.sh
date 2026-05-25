#!/usr/bin/env bash
# MKV data transport — abuse H.264/H.265 video codec as a lossless compressor
# via FFmpeg, with hardware acceleration where available.
set -euo pipefail

INPUT="${1:-/dev/stdin}"
OUTPUT="${2:-/tmp/mkv-transport.mkv}"
CODEC="${3:-libx264}"    # libx264, libx265, h264_nvenc, hevc_nvenc, av1_nvenc
QP="${QP:-0}"            # 0 = lossless (for libx264/libx265)
WIDTH="${WIDTH:-1920}"
HEIGHT="${HEIGHT:-1080}"
FPS="${FPS:-30}"

echo "[mkv-transport] Encoding $INPUT → $OUTPUT (codec=$CODEC qp=$QP ${WIDTH}x${HEIGHT})"

# Pack raw data as RGBA video frames → MKV container
# Each video frame holds WIDTH*HEIGHT*4 bytes of data
# Use -qp 0 for lossless H.264/H.265 encoding
# For NVENC: -cq 0 works similarly

case "$CODEC" in
  libx264)
      ENC_ARGS="-c:v libx264 -qp $QP -preset ultrafast -pix_fmt rgba"
    ;;
  libx265)
    ENC_ARGS="-c:v libx265 -x265-params lossless=1 -pix_fmt rgba"
    ;;
  h264_nvenc)
    ENC_ARGS="-c:v h264_nvenc -cq $QP -preset p1 -pix_fmt rgba"
    ;;
  hevc_nvenc)
    ENC_ARGS="-c:v hevc_nvenc -cq $QP -preset p1 -pix_fmt rgba"
    ;;
  av1_nvenc)
    ENC_ARGS="-c:v av1_nvenc -cq $QP -preset p1 -pix_fmt rgba"
    ;;
  *)
    echo "Unknown codec: $CODEC"
    exit 1
    ;;
esac

ffmpeg -y -f rawvideo -pix_fmt rgba -s "${WIDTH}x${HEIGHT}" -r "$FPS" -i "$INPUT" \
  -f matroska $ENC_ARGS -an -sn "$OUTPUT" 2>&1

echo "[mkv-transport] Done: $(stat -c%s "$OUTPUT" 2>/dev/null || echo 0) bytes"
