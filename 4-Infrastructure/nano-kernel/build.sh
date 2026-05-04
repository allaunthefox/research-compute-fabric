#!/bin/bash
set -e
BUILD="$(cd "$(dirname "$0")" && pwd)/build"
INITRAMFS="$BUILD/initramfs"
mkdir -p "$INITRAMFS"

# Build minimal kernel
echo "[*] Building kernel..."
cp nano-kernel.config /usr/src/linux/.config 2>/dev/null || true
cd /usr/src/linux && make oldconfig && make -j$(nproc) bzImage
cp arch/x86/boot/bzImage "$BUILD/"

# Build initramfs
echo "[*] Building initramfs..."
cp init "$INITRAMFS/"
chmod +x "$INITRAMFS/init"
gcc -static -o "$INITRAMFS/bin/socket-server" socket-server.c

# Create cpio archive
cd "$INITRAMFS"
find . | cpio -H newc -o | gzip -9 > "$BUILD/initramfs.cpio.gz"

echo "[*] Done: $BUILD/bzImage + $BUILD/initramfs.cpio.gz"
