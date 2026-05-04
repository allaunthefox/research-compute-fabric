# OTOM Static Compilation Suite
# Makefile for static builds of Lean 4 executables
#
# Targets:
#   all           - Build all static executables
#   static        - Build with static linking (default)
#   docker-build  - Build inside Docker container
#   release       - Optimized release build
#   cross-linux   - Cross-compile for Linux targets
#   check         - Verify toolchain
#   lint          - Run zero-trust linter
#   clean         - Remove build artifacts
#
# Configuration via environment variables:
#   LEAN_CC       - C compiler to use (default: gcc)
#   STATIC_FLAGS  - Static linker flags (default: -static)
#   BUILD_DIR     - Build output directory (default: ./build-static/out)

.PHONY: all static docker-build release cross-linux check lint clean

# Default target
all: static

# Configuration
PROJECT_ROOT := $(shell cd ../../../.. && pwd)
SEMANTICS_DIR := $(PROJECT_ROOT)/0-Core-Formalism/lean/Semantics
BUILD_DIR ?= $(SEMANTICS_DIR)/build-static/out
LEAN_CC ?= gcc
STATIC_FLAGS ?= -static -static-libgcc
LAKE := lake

# Executables from lakefile.toml
EXECUTABLES := bindserver searchserver SemanticsCli openworm_benchmark \
               ExtremeParameterTestEval NominalParameterTestEval moim_benchmark \
               generate_sparkle_phi_s3c tangnano9k_emitter

# Static build: compile all executables with static linking
static: check
	@echo "=== OTOM Static Compilation Suite ==="
	@echo "Toolchain: $(LEAN_CC)"
	@echo "Static flags: $(STATIC_FLAGS)"
	@echo "Build dir: $(BUILD_DIR)"
	@echo ""
	mkdir -p "$(BUILD_DIR)"
	cd "$(SEMANTICS_DIR)" && \
		LEAN_CC="$(LEAN_CC)" \
		LEANC_OPTS="$(STATIC_FLAGS) -O2" \
		$(LAKE) build $(EXECUTABLES)
	@echo ""
	@echo "=== Static build complete ==="
	@ls -la "$(SEMANTICS_DIR)/.lake/build/bin/" 2>/dev/null || true

# Release build: optimized static build with LTO
release: check
	@echo "=== OTOM Release Build (Optimized + LTO) ==="
	mkdir -p "$(BUILD_DIR)"
	cd "$(SEMANTICS_DIR)" && \
		LEAN_CC="$(LEAN_CC)" \
		LEANC_OPTS="$(STATIC_FLAGS) -O3 -flto -fwhole-program -ffunction-sections -fdata-sections" \
		$(LAKE) build $(EXECUTABLES)
	@echo "=== Release build complete ==="

# Docker-based reproducible build
docker-build:
	@echo "=== Docker Static Build ==="
	docker build -t otom-lean-static -f "$(SEMANTICS_DIR)/build-static/Dockerfile.static" "$(PROJECT_ROOT)"
	docker run --rm \
		-v "$(PROJECT_ROOT):/workspace" \
		-e BUILD_DIR=/workspace/build-static/out \
		otom-lean-static \
		make -C /workspace/0-Core-Formalism/lean/Semantics/build-static static

# Cross-compilation for Linux targets
cross-linux: check
	@echo "=== Cross-compilation for Linux ==="
	cd "$(SEMANTICS_DIR)" && \
		LEAN_CC="$(LEAN_CC)" \
		LEANC_OPTS="$(STATIC_FLAGS) -O2 -march=x86-64 -mtune=generic" \
		$(LAKE) build $(EXECUTABLES)

# Toolchain verification
check:
	@echo "=== Toolchain Check ==="
	@command -v $(LEAN_CC) >/dev/null 2>&1 || { echo "ERROR: $(LEAN_CC) not found"; exit 1; }
	@command -v $(LAKE) >/dev/null 2>&1 || { echo "ERROR: lake not found"; exit 1; }
	@command -v lean >/dev/null 2>&1 || { echo "ERROR: lean not found"; exit 1; }
	@echo "GCC:    $$($(LEAN_CC) --version | head -1)"
	@echo "Lake:   $$($(LAKE) --version | head -1)"
	@echo "Lean:   $$(lean --version)"
	@echo "Static: $$($(LEAN_CC) -static -dumpspecs 2>/dev/null | grep -c 'crtbeginT' || echo 'check manually')"
	@echo ""
	@echo "All tools available."

# Zero-trust linter
lint:
	@echo "=== Zero-Trust Linter ==="
	cd "$(SEMANTICS_DIR)" && ./scripts/zero_trust_linter.sh

# Verilog emission for FPGA targets
verilog:
	@echo "=== Verilog Emission (Tang Nano 9K) ==="
	cd "$(SEMANTICS_DIR)" && $(LAKE) exe tangnano9k_emitter
	cd "$(SEMANTICS_DIR)" && $(LAKE) exe generate_sparkle_phi_s3c

# FPGA synthesis (requires yosys, nextpnr, gowin_pack)
synthesis: verilog
	@echo "=== FPGA Synthesis ==="
	cd "$(PROJECT_ROOT)/5-Applications/out/verilog" && ./build_tangnano9k.sh

# Clean build artifacts
clean:
	@echo "=== Cleaning ==="
	cd "$(SEMANTICS_DIR)" && $(LAKE) clean || true
	rm -rf "$(BUILD_DIR)"
	@echo "Clean complete."

# Install static binaries to BUILD_DIR
install: static
	@echo "=== Installing to $(BUILD_DIR) ==="
	mkdir -p "$(BUILD_DIR)"
	cp "$(SEMANTICS_DIR)/.lake/build/bin/"* "$(BUILD_DIR)/" 2>/dev/null || true
	@echo "Installed:"
	@ls -la "$(BUILD_DIR)/"

# Help target
help:
	@echo "OTOM Static Compilation Suite"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' || \
	grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | grep -v '^\.PHONY' | sed 's/:.*//' | sort | awk '{printf "  %-15s\n", $$1}'
