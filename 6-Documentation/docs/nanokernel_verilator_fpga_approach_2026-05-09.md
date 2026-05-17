# Nanokernel + Verilator FPGA Programming Approach
**Date:** 2026-05-09
**Objective:** Bypass Gowin toolchain fragmentation using nanokernel + Verilator

---

## Problem Analysis

**Current Issue:** Gowin toolchain fragmentation prevents bitstream generation
- Yosys synth_gowin generates JSON incompatible with gowin_pack
- nextpnr-himbaechel has device naming and package specification issues
- No unified open-source workflow for Gowin GW1N-9C FPGA

**Root Cause:** Toolchain ecosystem fragmentation
- Each tool expects different JSON formats
- Device naming conventions inconsistent
- Package specification not standardized

---

## New Approach: Nanokernel + Verilator

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Host System (Linux)                                         │
│ ├─ Nanokernel (~1.5MB)                                     │
│ │  ├─ GCL bytecode interpreter                            │
│ │  ├─ UART communication layer                             │
│ │  ├─ Memory arena allocator                               │
│ │  └─ Verification hooks (Lean)                            │
│ ├─ Verilator (Simulation & Verification)                   │
│ └─ FTDI Interface (USB-FT2232C)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (UART 115200 baud)
┌─────────────────────────────────────────────────────────────┐
│ FPGA (Gowin GW1NR-9 / Tang Nano 9K)                        │
│ ├─ Simple UART loader (minimal bitstream)                   │
│ ├─ Meta-Manifold Prover logic                               │
│ └─ Direct programming interface                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Innovations

**1. Nanokernel as FPGA Loader**
- Use nanokernel's minimal syscall interface for FPGA management
- UART-based programming bypasses complex Gowin toolchain
- GCL bytecode ensures verifiable, traceable operations

**2. Verilator for Verification**
- Simulate Meta-Manifold Prover before hardware deployment
- Verify timing, correctness, and resource usage
- Generate test vectors for hardware validation

**3. Direct UART Programming**
- Program FPGA via existing FTDI FT2232C interface
- Use simple binary protocol (no complex bitstream format)
- Leverage existing UART stack from nanokernel

---

## Implementation Plan

### Phase 1: Nanokernel UART FPGA Loader

**File:** `4-Infrastructure/nano-kernel/fpga_uart_loader.gcl`

```
# GCL Nanokernel FPGA UART Loader
# Purpose: Program FPGA via UART without Gowin toolchain

function fpgaOpenDevice(device_path):
    # Open FTDI device
    syscall network_send device_path
    return device_handle

function fpgaSendByte(handle, byte):
    # Send single byte via UART
    syscall network_send byte
    return success

function fpgaReceiveByte(handle):
    # Receive single byte via UART
    syscall network_receive
    return byte

function fpgaProgramBitstream(handle, bitstream):
    # Program FPGA with bitstream
    for each byte in bitstream:
        fpgaSendByte(handle, byte)
        ack = fpgaReceiveByte(handle)
        if ack != 0xFA:
            return error
    return success

function fpgaVerify(handle, expected_state):
    # Verify FPGA state
    fpgaSendByte(handle, 0x00)  # Status request
    state = fpgaReceiveByte(handle)
    return state == expected_state
```

**Size Estimate:** ~500 bytes GCL bytecode

### Phase 2: Verilator Testbench for Meta-Manifold Prover

**File:** `4-Infrastructure/hardware/tb_metamanifold_prover.cpp`

```cpp
/*
 * Verilator testbench for Meta-Manifold Prover
 * Validates: Mass Number gates, Torus topology, Menger sponge, Fold energy
 */

#include "VMetaManifoldProver.h"
#include <cstdio>

int main(int argc, char** argv) {
    VerilatedContext* contextp = new VerilatedContext;
    contextp->commandArgs(argc, argv);

    VMetaManifoldProver* top = new VMetaManifoldProver{contextp};

    // Initialize inputs
    top->clk = 0;
    top->rst_n = 0;
    top->start = 0;

    // Release reset
    for (int i = 0; i < 100; i++) {
        top->clk = !top->clk;
        top->eval();
    }
    top->rst_n = 1;

    // Test Mass Number Gate
    top->op_select = 3'b000;  // MassLe operation
    top->admissible = 16'h1000;  // Q16_16: 1.0
    top->residual = 16'h0800;    // Q16_16: 0.5
    top->epsilon = 16'h0100;     // Q16_16: 0.0625
    top->threshold = 16'h2000;   // Q16_16: 2.0
    top->start = 1;

    // Run operation
    for (int i = 0; i < 1000; i++) {
        top->clk = !top->clk;
        top->eval();
        if (top->done) break;
    }

    // Verify result
    printf("Mass Number Gate Result: %d\n", top->mass_le_result);

    delete top;
    delete contextp;
    return 0;
}
```

### Phase 3: Minimal FPGA Bitstream Format

**Format:** Simple binary protocol (no Gowin .fs format)

```
Header (4 bytes):
  0x47 0x43 0x4C 0x46  // "GCLF" magic number
  Length (4 bytes)     // Bitstream length in bytes

Data:
  Configuration bits
  LUT initialization
  Routing configuration

Footer (4 bytes):
  0x00 0x00 0x00 0x00  // End marker
```

**Advantages:**
- No dependency on Gowin proprietary format
- Simple to generate from Verilator simulation
- Direct mapping to FPGA configuration memory

### Phase 4: Nanokernel Integration

**Syscall Extensions:**
```
fpga_open(device_path) -> handle
fpga_write(handle, data, length) -> bytes_written
fpga_read(handle, buffer, length) -> bytes_read
fpga_close(handle) -> success
```

**Total syscall surface:** +4 syscalls (~200 bytes)

---

## Advantages Over Gowin Toolchain

### 1. Minimal Dependencies
- **Gowin approach:** Yosys + gowin_pack + nextpnr-himbaechel (3 tools, incompatible)
- **Nanokernel approach:** Verilator + nanokernel (2 tools, compatible)

### 2. Verifiable Operations
- **Gowin approach:** Black-box bitstream generation
- **Nanokernel approach:** GCL bytecode with Lean verification hooks

### 3. Traceable Execution
- **Gowin approach:** No execution tracing
- **Nanokernel approach:** Every syscall logged with BindResult witness

### 4. Recoverable from Errors
- **Gowin approach:** Toolchain errors are unrecoverable
- **Nanokernel approach:** Linux shim can recover from GCL failures

---

## Implementation Steps

### Step 1: Create Verilator Testbench
- [ ] Write `tb_metamanifold_prover.cpp` testbench
- [ ] Add Makefile for Verilator build
- [ ] Verify Meta-Manifold Prover simulates correctly

### Step 2: Extract Configuration from Verilator
- [ ] Use Verilator's --emit-c option to extract configuration
- [ ] Generate simple binary bitstream format
- [ ] Validate bitstream format

### Step 3: Implement Nanokernel FPGA Loader
- [ ] Write `fpga_uart_loader.gcl`
- [ ] Add FPGA syscalls to Linux shim
- [ ] Compile and test nanokernel

### Step 4: Integrate and Test
- [ ] Connect nanokernel to FPGA via UART
- [ ] Program FPGA with new bitstream
- [ ] Verify Meta-Manifold Prover operations

---

## Expected Results

### Size Comparison

| Component | Gowin Approach | Nanokernel Approach | Savings |
|-----------|---------------|---------------------|---------|
| Toolchain | ~500MB (Yosys + Gowin) | ~50MB (Verilator + GCL) | **450MB** |
| Bitstream | ~2MB (Gowin .fs) | ~500KB (simple format) | **1.5MB** |
| Loader | ~10MB (openFPGALoader) | ~1.5MB (nanokernel) | **8.5MB** |
| **Total** | **~512MB** | **~52MB** | **~460MB (90%)** |

### Verification Coverage

| Aspect | Gowin Approach | Nanokernel Approach |
|--------|---------------|---------------------|
| Formal verification | ❌ None | ✅ Lean equivalence |
| Execution tracing | ❌ None | ✅ BindResult witness |
| Error recovery | ❌ None | ✅ Linux shim fallback |
| Minimal surface | ❌ 300+ syscalls | ✅ 12 syscalls |

---

## Risks and Mitigations

### Risk 1: FPGA Configuration Memory Access
**Issue:** Direct configuration memory access may be undocumented
**Mitigation:** Use existing UART loader pattern from Gowin tools as reference

### Risk 2: Timing Constraints
**Issue:** Nanokernel may not meet real-time constraints for programming
**Mitigation:** Use nanokernel's memory arena allocator for deterministic timing

### Risk 3: Bitstream Compatibility
**Issue:** Simple format may not support all FPGA features
**Mitigation:** Start with minimal feature set (LUTs only), expand as needed

---

## Success Criteria

1. **Verilator Simulation:** Meta-Manifold Prover simulates correctly
2. **Bitstream Generation:** Simple binary format generates successfully
3. **Nanokernel Loader:** FPGA programs via UART without errors
4. **Hardware Verification:** Meta-Manifold Prover operations work on hardware
5. **Size Reduction:** Total toolchain size < 100MB (vs 512MB Gowin)

---

## Next Actions

1. Create Verilator testbench for Meta-Manifold Prover
2. Extract configuration from Verilator simulation
3. Implement nanokernel FPGA loader in GCL
4. Test on actual FPGA hardware

**Status:** Design complete, ready for implementation
