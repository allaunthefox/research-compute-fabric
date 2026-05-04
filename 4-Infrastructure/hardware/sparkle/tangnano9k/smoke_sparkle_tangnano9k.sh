#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT="${SPARKLE_UART_PORT:-/dev/ttyUSB1}"
SECONDS="${SPARKLE_UART_SECONDS:-5}"
MIN_FRAMES="${SPARKLE_UART_MIN_FRAMES:-1}"

./build_sparkle_tangnano9k.sh --flash-sram
./monitor_uart.py "${PORT}" --seconds "${SECONDS}" --expect-state-tag --min-frames "${MIN_FRAMES}"
