# QFox Topology Manager kernel module
#
# Builds out-of-tree against the running kernel by default. CachyOS builds the
# stock kernel with clang/LLVM, so LLVM=1 is the default here too.

KVER ?= $(shell uname -r)
KDIR ?= /usr/lib/modules/$(KVER)/build

LLVM ?= 1
CC ?= clang
ifeq ($(origin CC),default)
CC := clang
endif

obj-m += qfox_topology_manager.o
ccflags-y += -g

all:
	$(MAKE) CC=$(CC) LLVM=$(LLVM) -C $(KDIR) M=$(CURDIR) modules

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean

load:
	sudo modprobe qfox_topology_manager || sudo insmod qfox_topology_manager.ko

unload:
	sudo modprobe -r qfox_topology_manager || sudo rmmod qfox_topology_manager

info:
	modinfo qfox_topology_manager.ko

debug-attach:
	sudo ./qfox_topology_debug.sh attach

debug-snapshot:
	sudo ./qfox_topology_debug.sh snapshot

debug-detach:
	sudo ./qfox_topology_debug.sh detach

.PHONY: all clean load unload info debug-attach debug-snapshot debug-detach
