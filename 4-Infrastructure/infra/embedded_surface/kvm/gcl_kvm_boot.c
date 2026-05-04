/*
 * gcl_kvm_boot.c
 *
 * Minimal userspace KVM surface runner. This intentionally follows the spirit
 * of kvm-hello-world: open /dev/kvm, create a VM, map memory, create one VCPU,
 * run tiny guest code, capture an I/O port pulse, and halt.
 */

#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <linux/kvm.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define CHECK(expr, msg) \
    do { \
        if ((expr) < 0) { \
            perror(msg); \
            return 1; \
        } \
    } while (0)

enum {
    GUEST_MEM_SIZE = 0x10000,
    GUEST_CODE_ADDR = 0x1000,
    DEBUG_PORT = 0xE9,
};

static const char pulse[] =
    "GCLKVM v0.1\n"
    "surface=node kind=kvm.boot op=recover\n"
    "kvm memslot=0 guest_phys=0x00000000 entry=0x00001000 io=0x00E9\n"
    "ot1 op=0x0D source=0x002A route=0x0001 seq=0x0001\n"
    "gcl admission=admitted invariant=recovery_subset\n"
    "BOOT_OK\n";

static int emit_guest_code(uint8_t *mem, size_t mem_size) {
    uint8_t *code = mem + GUEST_CODE_ADDR;
    size_t off = 0;

    if (GUEST_CODE_ADDR + (sizeof(pulse) * 4) + 1 >= mem_size) {
        fprintf(stderr, "guest memory too small\n");
        return -1;
    }

    for (size_t i = 0; pulse[i] != '\0'; i++) {
        code[off++] = 0xB0;                 /* mov imm8, %al */
        code[off++] = (uint8_t)pulse[i];
        code[off++] = 0xE6;                 /* out %al, imm8 */
        code[off++] = DEBUG_PORT;
    }
    code[off++] = 0xF4;                     /* hlt */
    return 0;
}

static int setup_real_mode(int vcpu_fd) {
    struct kvm_sregs sregs;
    struct kvm_regs regs;

    CHECK(ioctl(vcpu_fd, KVM_GET_SREGS, &sregs), "KVM_GET_SREGS");
    sregs.cs.selector = 0;
    sregs.cs.base = 0;
    CHECK(ioctl(vcpu_fd, KVM_SET_SREGS, &sregs), "KVM_SET_SREGS");

    memset(&regs, 0, sizeof(regs));
    regs.rflags = 0x2;
    regs.rip = GUEST_CODE_ADDR;
    CHECK(ioctl(vcpu_fd, KVM_SET_REGS, &regs), "KVM_SET_REGS");
    return 0;
}

int main(void) {
    int ret = 1;
    int kvm_fd = -1;
    int vm_fd = -1;
    int vcpu_fd = -1;
    uint8_t *guest_mem = MAP_FAILED;
    struct kvm_run *run = MAP_FAILED;

    kvm_fd = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    CHECK(kvm_fd, "open /dev/kvm");

    int api_version = ioctl(kvm_fd, KVM_GET_API_VERSION, 0);
    if (api_version != KVM_API_VERSION) {
        fprintf(stderr, "unsupported KVM API version %d\n", api_version);
        goto cleanup;
    }

    vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);
    CHECK(vm_fd, "KVM_CREATE_VM");

    guest_mem = mmap(NULL, GUEST_MEM_SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
    if (guest_mem == MAP_FAILED) {
        perror("mmap guest memory");
        goto cleanup;
    }
    memset(guest_mem, 0, GUEST_MEM_SIZE);
    if (emit_guest_code(guest_mem, GUEST_MEM_SIZE) != 0) {
        goto cleanup;
    }

    struct kvm_userspace_memory_region region = {
        .slot = 0,
        .flags = 0,
        .guest_phys_addr = 0,
        .memory_size = GUEST_MEM_SIZE,
        .userspace_addr = (uint64_t)guest_mem,
    };
    CHECK(ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region), "KVM_SET_USER_MEMORY_REGION");

    vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);
    CHECK(vcpu_fd, "KVM_CREATE_VCPU");

    int vcpu_mmap_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
    CHECK(vcpu_mmap_size, "KVM_GET_VCPU_MMAP_SIZE");
    run = mmap(NULL, (size_t)vcpu_mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED, vcpu_fd, 0);
    if (run == MAP_FAILED) {
        perror("mmap kvm_run");
        goto cleanup;
    }

    if (setup_real_mode(vcpu_fd) != 0) {
        goto cleanup;
    }

    for (;;) {
        CHECK(ioctl(vcpu_fd, KVM_RUN, 0), "KVM_RUN");
        switch (run->exit_reason) {
        case KVM_EXIT_HLT:
            ret = 0;
            goto cleanup;
        case KVM_EXIT_IO:
            if (run->io.direction == KVM_EXIT_IO_OUT &&
                run->io.port == DEBUG_PORT &&
                run->io.size == 1) {
                uint8_t *data = (uint8_t *)run + run->io.data_offset;
                for (uint32_t i = 0; i < run->io.count; i++) {
                    putchar(data[i]);
                }
                fflush(stdout);
            } else {
                fprintf(stderr, "unexpected IO exit: port=0x%x direction=%u size=%u\n",
                        run->io.port, run->io.direction, run->io.size);
                goto cleanup;
            }
            break;
        default:
            fprintf(stderr, "unexpected KVM exit reason %u\n", run->exit_reason);
            goto cleanup;
        }
    }

cleanup:
    if (run != MAP_FAILED) {
        int vcpu_mmap_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
        if (vcpu_mmap_size > 0) {
            munmap(run, (size_t)vcpu_mmap_size);
        }
    }
    if (guest_mem != MAP_FAILED) {
        munmap(guest_mem, GUEST_MEM_SIZE);
    }
    if (vcpu_fd >= 0) {
        close(vcpu_fd);
    }
    if (vm_fd >= 0) {
        close(vm_fd);
    }
    if (kvm_fd >= 0) {
        close(kvm_fd);
    }
    return ret;
}
