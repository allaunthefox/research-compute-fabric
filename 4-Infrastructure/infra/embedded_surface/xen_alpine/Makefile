BUILD_DIR := build
STATIC_BIN := $(BUILD_DIR)/rs-surface-static
NOLIBC_BIN := $(BUILD_DIR)/rs-surface-nolibc
CC ?= cc
STATIC_CFLAGS ?= -std=c11 -Os -Wall -Wextra -march=x86-64 -mtune=generic -mno-avx -mno-avx2 -ffunction-sections -fdata-sections
STATIC_LDFLAGS ?= -static -Wl,--gc-sections
NOLIBC_CFLAGS ?= -std=c11 -Os -Wall -Wextra -march=x86-64 -mtune=generic -mno-avx -mno-avx2 -ffreestanding -fno-stack-protector -fno-pic -fno-pie -fno-asynchronous-unwind-tables -fno-unwind-tables -nostdlib -static

.PHONY: check smoke qemu-smoke qemu-static-smoke static clean

check:
	python3 -m py_compile smoke_xen_alpine_surface.py ../server.py
	python3 -m json.tool ../profiles/xen-alpine-surface.json >/dev/null
	sh -n install_rs_surface_openrc.sh
	sh -n rs-surface.openrc
	sh -n run_qemu_alpine_surface.sh
	$(CC) $(STATIC_CFLAGS) -fsyntax-only rs_surface_static.c
	$(CC) $(NOLIBC_CFLAGS) -fsyntax-only rs_surface_nolibc.c

smoke:
	python3 smoke_xen_alpine_surface.py --host 127.0.0.1 --port 8080

qemu-smoke:
	./run_qemu_alpine_surface.sh

qemu-static-smoke: nolibc
	SURFACE_IMPL=nolibc ./run_qemu_alpine_surface.sh

static: $(STATIC_BIN)

nolibc: $(NOLIBC_BIN)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(STATIC_BIN): rs_surface_static.c | $(BUILD_DIR)
	$(CC) $(STATIC_CFLAGS) -o $@ $< $(STATIC_LDFLAGS)
	strip $@ || true
	ls -lh $@

$(NOLIBC_BIN): rs_surface_nolibc.c | $(BUILD_DIR)
	$(CC) $(NOLIBC_CFLAGS) -Wl,--build-id=none -Wl,-n -o $@ $<
	strip $@ || true
	ls -lh $@

clean:
	rm -rf $(BUILD_DIR)
