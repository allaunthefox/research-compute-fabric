BUILD_DIR := build
BOOT_BIN := $(BUILD_DIR)/gcl_boot.bin
BOOT_ELF := $(BUILD_DIR)/gcl_boot.elf
BOOT_OBJ := $(BUILD_DIR)/gcl_boot.o

.PHONY: all array clean dodgy run

all: $(BOOT_BIN)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BOOT_OBJ): gcl_boot.S | $(BUILD_DIR)
	as --32 -o $@ $<

$(BOOT_ELF): $(BOOT_OBJ)
	ld -m elf_i386 -Ttext 0 --oformat elf32-i386 -nostdlib -o $@ $<

$(BOOT_BIN): $(BOOT_ELF)
	objcopy -O binary -j .text $< $@

run: $(BOOT_BIN)
	./run_qemu_boot.sh

array: $(BOOT_BIN)
	./qemu_array_harness.py --count 10

dodgy: $(BOOT_BIN)
	./qemu_array_harness.py --scenario dodgy

clean:
	rm -rf $(BUILD_DIR)
