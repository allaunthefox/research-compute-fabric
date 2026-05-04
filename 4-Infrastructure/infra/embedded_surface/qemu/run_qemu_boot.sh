#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

make build/gcl_boot.bin >/dev/null

log="build/gcl_boot.serial.log"
rm -f "$log"

timeout 5s qemu-system-x86_64 \
  -machine accel=tcg \
  -m 8M \
  -display none \
  -no-reboot \
  -drive format=raw,file=build/gcl_boot.bin,if=floppy,readonly=on \
  -serial "file:$log" \
  -monitor none \
  -no-shutdown || status=$?

status="${status:-0}"
if [ "$status" != "0" ] && [ "$status" != "124" ]; then
  echo "qemu exited with status $status" >&2
  exit "$status"
fi

cat "$log"

grep -q "BOOT_OK" "$log"
