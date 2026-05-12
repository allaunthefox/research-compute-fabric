# PIST Topological Compression Kernel Module Makefile
# Build against linux-cachyos headers (kernel built with clang)

KVER ?= 7.0.3-1-cachyos
KDIR ?= /usr/lib/modules/$(KVER)/build

CC = clang
LLVM = 1

obj-m += pist_neuromorphic.o

all:
	$(MAKE) CC=$(CC) LLVM=$(LLVM) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

load:
	sudo insmod pist_neuromorphic.ko

unload:
	sudo rmmod pist_neuromorphic

info:
	modinfo pist_neuromorphic.ko

.PHONY: all clean load unload info
