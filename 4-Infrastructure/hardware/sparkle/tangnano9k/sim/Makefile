# Verilator simulation Makefile for SparkleTangNano9KTop
# Usage:
#   make         — build and run simulation
#   make trace   — build and run with VCD waveform dump
#   make clean   — remove build artifacts

TOP := SparkleTangNano9KTop
PWD := $(shell pwd)
RTL_TOP := "$(PWD)/../SparkleTangNano9KTop.v"
RTL_PAYLOAD := "$(PWD)/../../generated/sparkle_phi_s3c_payload.sv"
TB_CPP := "$(PWD)/tb_$(TOP).cpp"

BUILD_DIR := /tmp/verilator_sparkle_sim
SIM_BIN := $(BUILD_DIR)/V$(TOP)

# Verilator flags
VERILATOR := verilator
VERILATOR_FLAGS := -Wall -Wpedantic -Wno-fatal \
	-cc --exe --build --trace \
	-Mdir $(BUILD_DIR) \
	--top-module $(TOP)

# Source files (absolute paths)
VSRCS := $(RTL_TOP) $(RTL_PAYLOAD)

.PHONY: all trace run clean

all: $(SIM_BIN)
	./$(SIM_BIN)

trace: $(SIM_BIN)
	TRACE=1 ./$(SIM_BIN)

$(SIM_BIN): $(VSRCS) $(TB_CPP)
	$(VERILATOR) $(VERILATOR_FLAGS) $(VSRCS) $(TB_CPP)
	mv $(BUILD_DIR)/V$(TOP) $(SIM_BIN)

run: $(SIM_BIN)
	./$(SIM_BIN)

clean:
	rm -rf $(BUILD_DIR) *.vcd
