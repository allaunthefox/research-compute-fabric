BUILD_DIR := build
KVM_BOOT := $(BUILD_DIR)/gcl_kvm_boot

.PHONY: all array clean run

all: $(KVM_BOOT)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(KVM_BOOT): gcl_kvm_boot.c | $(BUILD_DIR)
	cc -std=c11 -Wall -Wextra -O2 -o $@ $<

run: $(KVM_BOOT)
	./$(KVM_BOOT)

array: $(KVM_BOOT)
	./kvm_array_harness.py --count 10

clean:
	rm -rf $(BUILD_DIR)
