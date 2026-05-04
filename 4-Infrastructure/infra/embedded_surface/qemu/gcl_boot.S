/*
 * gcl_boot.S
 *
 * Minimal x86 BIOS boot sector for the embedded surface boot-cycle smoke test.
 * It does not boot Linux. It initializes COM1, emits a GCL/Omnitoken recovery
 * pulse, then halts. The whole artifact is one 512-byte boot sector.
 */

.code16
.global _start

COM1 = 0x3f8

_start:
    cli
    movw $0x07c0, %ax
    movw %ax, %ds
    movw %ax, %es
    xorw %ax, %ax
    movw %ax, %ss
    movw $0x7c00, %sp
    sti

    call serial_init

    movw $msg_boot, %si
    call serial_puts

halt_loop:
    hlt
    jmp halt_loop

serial_init:
    movw $(COM1 + 1), %dx
    movb $0x00, %al
    outb %al, %dx

    movw $(COM1 + 3), %dx
    movb $0x80, %al
    outb %al, %dx

    movw $(COM1 + 0), %dx
    movb $0x03, %al
    outb %al, %dx

    movw $(COM1 + 1), %dx
    movb $0x00, %al
    outb %al, %dx

    movw $(COM1 + 3), %dx
    movb $0x03, %al
    outb %al, %dx

    movw $(COM1 + 2), %dx
    movb $0xc7, %al
    outb %al, %dx

    movw $(COM1 + 4), %dx
    movb $0x0b, %al
    outb %al, %dx
    ret

serial_putc:
    pushw %ax
    movw $(COM1 + 5), %dx
1:
    inb %dx, %al
    testb $0x20, %al
    jz 1b
    movw $(COM1 + 0), %dx
    popw %ax
    outb %al, %dx
    ret

serial_puts:
    lodsb
    testb %al, %al
    jz 1f
    call serial_putc
    jmp serial_puts
1:
    ret

msg_boot:
    .ascii "GCLBOOT v0.1\r\n"
    .ascii "surface=node kind=qemu.boot op=recover\r\n"
    .ascii "ot1 op=0x0D source=0x002A route=0x0001 seq=0x0001\r\n"
    .ascii "gcl admission=admitted invariant=recovery_subset\r\n"
    .ascii "BOOT_OK\r\n"
    .byte 0

    .org 510
    .word 0xaa55
