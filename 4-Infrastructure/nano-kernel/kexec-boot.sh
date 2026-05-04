#!/bin/bash
# kexec-boot.sh - Deploy nano kernel on RackNerd VPS
# Usage: ./kexec-boot.sh [nanokernel|restore]

set -e

NANO_DIR="/root/nano-kernel"
KERNEL_URL="https://github.com/allaunthefox/Research-Stack/releases/download/nano-kernel/bzImage"
INITRD_URL="https://github.com/allaunthefox/Research-Stack/releases/download/nano-kernel/initramfs.cpio.gz"

case "${1:-nanokernel}" in
    nanokernel)
        echo "[*] Preparing nano kernel boot..."
        
        # Download if not present
        if [[ ! -f "$NANO_DIR/bzImage" ]]; then
            echo "[*] Downloading nano kernel..."
            mkdir -p "$NANO_DIR"
            curl -L -o "$NANO_DIR/bzImage" "$KERNEL_URL"
        fi
        
        if [[ ! -f "$NANO_DIR/initramfs.cpio.gz" ]]; then
            echo "[*] Downloading initramfs..."
            curl -L -o "$NANO_DIR/initramfs.cpio.gz" "$INITRD_URL"
        fi
        
        # Backup current kernel for restore
        echo "[*] Backing up current kernel config..."
        cp /boot/vmlinuz-* "$NANO_DIR/vmlinuz-backup" 2>/dev/null || true
        
        # Load nano kernel via kexec
        echo "[*] Loading nano kernel..."
        kexec -l "$NANO_DIR/bzImage" \
            --initrd="$NANO_DIR/initramfs.cpio.gz" \
            --command-line="console=ttyS0,115200n8 console=tty0 quiet init=/init"
        
        echo "[*] Nano kernel loaded. Executing kexec..."
        echo "[*] Connection will drop. Reconnect in 30 seconds."
        echo "[*] SSH: ssh root@172.245.19.182 -p 8220"
        sleep 3
        
        # Execute kexec
        systemctl kexec || kexec -e
        ;;
        
    restore)
        echo "[*] Restoring standard kernel..."
        if [[ -f "$NANO_DIR/vmlinuz-backup" ]]; then
            kexec -l "$NANO_DIR/vmlinuz-backup" --reuse-cmdline
            systemctl kexec || kexec -e
        else
            echo "[!] No backup kernel found. Manual restore required."
            exit 1
        fi
        ;;
        
    status)
        echo "[*] Nano kernel status:"
        if [[ -f "$NANO_DIR/bzImage" ]]; then
            ls -lh "$NANO_DIR/bzImage"
        else
            echo "    bzImage: NOT PRESENT"
        fi
        if [[ -f "$NANO_DIR/initramfs.cpio.gz" ]]; then
            ls -lh "$NANO_DIR/initramfs.cpio.gz"
        else
            echo "    initramfs: NOT PRESENT"
        fi
        kexec -v 2>&1 | head -1
        ;;
        
    *)
        echo "Usage: $0 [nanokernel|restore|status]"
        exit 1
        ;;
esac
