#!/bin/bash
# qemu-test.sh - Boot nano kernel in QEMU (replicates RackNerd VPS environment)
# Usage: ./qemu-test.sh [build|boot|debug]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
QEMU_DIR="${SCRIPT_DIR}/qemu"

# QEMU configuration (matches RackNerd VPS specs)
QEMU_CPU="host"
QEMU_MEM="512M"           # Minimal - nanokernel uses <64MB
QEMU_NET="user,hostfwd=tcp::2222-:22,hostfwd=tcp::8220-:8220"  # SSH on 2222, socket on 8220
QEMU_DISK="${QEMU_DIR}/disk.img"
QEMU_KERNEL="${BUILD_DIR}/bzImage"
QEMU_INITRD="${BUILD_DIR}/initramfs.cpio.gz"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[QEMU]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check QEMU is installed
check_qemu() {
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        log_error "QEMU not found. Install with:"
        log_error "  sudo pacman -S qemu-full"
        exit 1
    fi
    
    log_info "QEMU found: $(qemu-system-x86_64 --version | head -1)"
    
    # Check for KVM acceleration
    if [ -c /dev/kvm ]; then
        log_info "KVM acceleration available"
        QEMU_ACCEL="-enable-kvm"
    else
        log_warn "KVM not available, using TCG (slower)"
        QEMU_ACCEL=""
    fi
}

# Create virtual disk for testing
create_disk() {
    mkdir -p "$QEMU_DIR"
    
    if [ ! -f "$QEMU_DISK" ]; then
        log_info "Creating virtual disk (128MB)..."
        qemu-img create -f raw "$QEMU_DISK" 128M
        
        # Format as ext4
        log_info "Formatting disk as ext4..."
        mkfs.ext4 "$QEMU_DISK"
        
        # Mount and copy Research Stack
        mkdir -p "${QEMU_DIR}/mnt"
        sudo mount "$QEMU_DISK" "${QEMU_DIR}/mnt"
        sudo mkdir -p "${QEMU_DIR}/mnt/research-stack"
        
        # Copy essential Research Stack files
        sudo cp -r "${SCRIPT_DIR}/../../0-Core-Formalism" "${QEMU_DIR}/mnt/research-stack/"
        
        sudo umount "${QEMU_DIR}/mnt"
        rmdir "${QEMU_DIR}/mnt"
    fi
    
    log_info "Virtual disk ready: $QEMU_DISK"
}

# Build kernel and initramfs if not present
build() {
    log_info "Building nano kernel..."
    
    if [ ! -f "$QEMU_KERNEL" ] || [ ! -f "$QEMU_INITRD" ]; then
        cd "$SCRIPT_DIR"
        ./build.sh
    fi
    
    if [ ! -f "$QEMU_KERNEL" ]; then
        log_error "Kernel not found: $QEMU_KERNEL"
        exit 1
    fi
    
    if [ ! -f "$QEMU_INITRD" ]; then
        log_error "Initramfs not found: $QEMU_INITRD"
        exit 1
    fi
    
    log_info "Kernel: $(ls -lh "$QEMU_KERNEL" | awk '{print $5}')"
    log_info "Initramfs: $(ls -lh "$QEMU_INITRD" | awk '{print $5}')"
}

# Boot nano kernel in QEMU
boot() {
    check_qemu
    
    if [ ! -f "$QEMU_KERNEL" ]; then
        build
    fi
    
    create_disk
    
    log_info "Booting nano kernel in QEMU..."
    log_info "SSH: ssh root@localhost -p 2222"
    log_info "Socket: nc localhost 8220"
    log_info "Console: Ctrl+A then X to quit"
    
    qemu-system-x86_64 \
        $QEMU_ACCEL \
        -cpu $QEMU_CPU \
        -m $QEMU_MEM \
        -kernel "$QEMU_KERNEL" \
        -initrd "$QEMU_INITRD" \
        -append "console=ttyS0,115200n8 root=/dev/ram0 quiet" \
        -netdev user,id=net0,$QEMU_NET \
        -device virtio-net-pci,netdev=net0 \
        -drive file="$QEMU_DISK",format=raw,if=virtio \
        -serial stdio \
        -nographic \
        -no-reboot \
        -no-shutdown
}

# Debug mode with GDB
debug() {
    check_qemu
    
    if [ ! -f "$QEMU_KERNEL" ]; then
        build
    fi
    
    log_info "Starting QEMU with GDB server (port 1234)..."
    log_info "Connect with: gdb -ex 'target remote localhost:1234'"
    
    qemu-system-x86_64 \
        $QEMU_ACCEL \
        -cpu $QEMU_CPU \
        -m $QEMU_MEM \
        -kernel "$QEMU_KERNEL" \
        -initrd "$QEMU_INITRD" \
        -append "console=ttyS0,115200n8 root=/dev/ram0 nokaslr" \
        -netdev user,id=net0,$QEMU_NET \
        -device virtio-net-pci,netdev=net0 \
        -serial stdio \
        -nographic \
        -s -S \
        -no-reboot \
        -no-shutdown
}

# Test socket interface
test_socket() {
    log_info "Testing socket interface on port 8220..."
    
    # Wait for QEMU to boot
    sleep 5
    
    # Test status command
    echo "status" | nc -q 1 localhost 8220
    
    # Test lake_build
    echo "lake_build" | nc -q 5 localhost 8220
}

# Main command handler
case "${1:-boot}" in
    build)
        build
        ;;
    boot)
        boot
        ;;
    debug)
        debug
        ;;
    test)
        test_socket
        ;;
    clean)
        log_info "Cleaning QEMU files..."
        rm -rf "$QEMU_DIR"
        ;;
    *)
        echo "Usage: $0 [build|boot|debug|test|clean]"
        echo ""
        echo "Commands:"
        echo "  build  - Build kernel and initramfs"
        echo "  boot   - Boot nano kernel in QEMU (default)"
        echo "  debug  - Start with GDB server"
        echo "  test   - Test socket interface"
        echo "  clean  - Remove QEMU files"
        exit 1
        ;;
esac
