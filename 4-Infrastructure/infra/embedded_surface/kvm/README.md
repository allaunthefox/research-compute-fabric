# Minimal KVM Surface

This directory contains a tiny userspace KVM runner for the embedded node
surface.

It is intentionally closer to `kvm-hello-world` than to QEMU:

```text
open /dev/kvm
KVM_CREATE_VM
mmap guest memory
KVM_SET_USER_MEMORY_REGION
KVM_CREATE_VCPU
KVM_RUN
capture out 0xE9
halt
```

## Addressing Rule

KVM addressing is not host physical addressing.

The runner owns host virtual memory, registers it as a KVM memslot, and exposes
that region to the guest as guest physical memory:

```text
host virtual pointer -> KVM memslot -> guest physical address -> guest CS:RIP
```

For this test:

```text
memslot          0
guest_phys_addr  0x00000000
memory_size      0x00010000
entry            0x00001000
debug io port    0x00E9
```

On a non-bare-metal VPS, there may be another hypervisor underneath this one.
That does not change the guest physical contract inside this process. It only
changes whether `/dev/kvm` exists, whether nested virtualization is enabled, and
which exits are slow or unavailable.

## Carrier Classes

The embedded surface should classify KVM like this:

| Class | Meaning | Action |
|-------|---------|--------|
| `kvm_native` | `/dev/kvm` works with hardware virtualization | Use KVM carrier |
| `kvm_nested` | `/dev/kvm` works inside a VM | Use KVM, expect slower exits |
| `kvm_unavailable` | `/dev/kvm` missing or permission denied | Fall back to QEMU TCG or hosted process |
| `kvm_restricted` | VM creation works but required exits fail | Fall back or quarantine |

GCL admission must happen before selecting the carrier. KVM is an execution
surface, not the root of trust.

## Commands

```bash
make -C infra/embedded_surface/kvm run
make -C infra/embedded_surface/kvm array
```
