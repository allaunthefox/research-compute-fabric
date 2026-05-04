# Nano Kernel Appliance - RackNerd VPS Deployment

**Target:** RackNerd VPS (172.245.19.182)  
**Purpose:** Minimal Linux kernel that boots directly into Research Stack swarm  
**Size Target:** ~10MB kernel + ~50MB initramfs (vs 200MB+ standard)

## Architecture

```
RackNerd VPS (172.245.19.182)
┌────────────────────────────────────────────────────────────┐
│ Standard Kernel (Debian/Ubuntu)                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ SSH in → run kexec-boot.sh                              │ │
│ │ Downloads nano-kernel + initramfs                      │ │
│ │ kexec -l bzImage --initrd=initramfs.cpio.gz            │ │
│ │ systemctl kexec                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                         │                                  │
│                         ▼                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Nano Kernel (5-10MB)                                    │ │
│ │ - x86_64 minimal                                        │ │
│ │ - VirtIO drivers only                                   │ │
│ │ - No graphics, no sound, minimal networking             │ │
│ └────────────────────────────────────────────────────────┘ │
│                         │                                  │
│                         ▼                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Initramfs (/init)                                       │ │
│ │ - Lean 4 lake build                                     │ │
│ │ - 89+ Semantics modules                                 │ │
│ │ - ENE node manager                                      │ │
│ │ - Socket server on port 8220                            │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Components

| File | Purpose | Target Size |
|------|---------|-------------|
| `nano-kernel.config` | Minimal kernel config | ~500 lines |
| `initramfs/` | Research Stack essentials | ~50MB compressed |
| `kexec-boot.sh` | Deploy and boot script | ~100 lines |
| `socket-server.c` | Nano kernel ↔ Host comms | ~500 lines |

## Deployment

```bash
# On local machine
./build-nano-kernel.sh
scp nano-kernel/* root@172.245.19.182:/root/nano-kernel/

# On RackNerd VPS
ssh root@172.245.19.182
cd /root/nano-kernel
./kexec-boot.sh
# VPS now runs nano kernel with Research Stack
```
