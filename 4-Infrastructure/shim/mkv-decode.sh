#!/usr/bin/env bash
# MKV data transport — decode
set -euo pipefail

INPUT="${1:-/tmp/mkv-transport.mkv}"
OUTPUT="${2:-/dev/stdout}"
WIDTH="${WIDTH:-1920}"
HEIGHT="${HEIGHT:-1080}"

ffmpeg -y -i "$INPUT" -f rawvideo -pix_fmt rgba -s "${WIDTH}x${HEIGHT}" -vframes 1 "$OUTPUT" 2>&1
