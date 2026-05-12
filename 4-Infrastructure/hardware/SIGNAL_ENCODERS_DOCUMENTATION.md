# Signal Theory Encoders Documentation

This document describes the hardware implementations of signal theory modules converted from Lean formalizations to Verilog, along with their simulation results using Verilator and ngspice.

## Overview

Two signal theory encoders have been implemented in Verilog and simulated:
1. **Spectral Encoder** - Implements spectral encoding theory from `Semantics/Spectrum.lean`
2. **Wavefront Emitter** - Implements wavefront emission theory from `Semantics/WavefrontEmitter.lean`

Both encoders use Q16.16 fixed-point arithmetic for hardware compatibility and have been verified through repeated simulation to ensure deterministic behavior.

---

## Spectral Encoder

### Theory Basis

The spectral encoder implements the spectral encoding theory formalized in `Semantics/Spectrum.lean`. Core concepts:

- **Spectral Signature**: 8-bin Q16.16 amplitude vector representing frequency domain information
- **Erdős-Hooley Constant**: δ ≈ 0.08607 (5643/65536 in Q16.16)
- **Spectral Overlap**: Inner product between spectral signatures
- **Piecewise Eigenvector Merge**: Superposition with saturation at 1.0
- **Genetic Event Mapping**: A, T, G, C events map to unique spectral bins

### Implementation

**File**: `spectral_encoder.v`

**Interface**:
```verilog
module spectral_encoder (
    input wire clk,
    input wire rst_n,
    input wire [7:0]  data_in,      // Input byte
    input wire        data_valid,
    input wire [2:0]  event_type,   // 0=A, 1=T, 2=G, 3=C
    output reg [15:0] bin0,         // 8 spectral bins
    output reg [15:0] bin1,
    output reg [15:0] bin2,
    output reg [15:0] bin3,
    output reg [15:0] bin4,
    output reg [15:0] bin5,
    output reg [15:0] bin6,
    output reg [15:0] bin7,
    output reg        spectral_valid
);
```

**Key Functions**:

1. **Spectral Overlap Calculation**:
   - Computes inner product between two spectral signatures
   - Uses Q16.16 multiplication with right shift for fixed-point arithmetic
   - Input: Two 8-bin spectral vectors
   - Output: 16-bit overlap value

2. **Piecewise Eigenvector Merge**:
   - Superposition of spectral values with saturation
   - Saturates at 16'h7FFF (1.0 in Q16.16)
   - Prevents overflow in accumulation

**Genetic Event Mapping**:
- Event A (type=0): Activates bin 0
- Event T (type=1): Activates bin 1
- Event G (type=2): Activates bin 2
- Event C (type=3): Activates bin 3

### Simulation Results

**Test Harness**: `spectral_encoder_tb.cpp`

**Test Cases**:
1. Event A: bin0 = 0x7FFF, others = 0x0000 ✓
2. Event T: bin1 = 0x7FFF, others = 0x0000 ✓
3. Event G: bin2 = 0x7FFF, others = 0x0000 ✓
4. Event C: bin3 = 0x7FFF, others = 0x0000 ✓
5. Accumulation (A then T): bin0-1 = 0x7FFF, others = 0x0000 ✓

**Convergence Testing**: 10 consecutive runs showed zero divergence - all runs produced identical results.

### Ngspice Circuit Simulation

**File**: `spectral_encoder_simple_spice.cir`

**Circuit Description**:
- 8 RC integrator circuits representing spectral bins
- Genetic events as pulse inputs (VA_IN, VT_IN, VG_IN, VC_IN)
- Each event charges its corresponding bin through resistor network
- R = 10kΩ, C = 10pF for each bin

**Simulation Results**:
- bin0_peak: 2.70234e+00 V at 1.22847e-07s
- bin1_peak: 2.70258e+00 V at 1.42958e-07s
- bin2_peak: 2.70260e+00 V at 1.62958e-07s
- bin3_peak: 2.70110e+00 V at 1.82700e-07s

**Convergence Testing**: 10 consecutive runs showed zero divergence in peak measurements and timing.

---

## Wavefront Emitter

### Theory Basis

The wavefront emitter implements wavefront emission theory formalized in `Semantics/WavefrontEmitter.lean`. Core concepts:

- **Wavefront Structure**: amplitude, frequency, phase, position
- **Wavefront Parameters**: default amplitude=1.0, frequency=0.1, speed=1.0, decay=0.01
- **Wavefront Computation**: Decay and oscillation based on distance
- **Wavefront Injection**: Emission into resonant field

### Implementation

**File**: `wavefront_emitter.v`

**Interface**:
```verilog
module wavefront_emitter (
    input wire clk,
    input wire rst_n,
    input wire [15:0] amplitude_in,      // Q16.16 amplitude
    input wire [15:0] frequency_in,      // Q16.16 frequency
    input wire [15:0] phase_in,         // Q16.16 phase
    input wire [15:0] position_x,       // Q16.16 x position
    input wire [15:0] position_y,       // Q16.16 y position
    input wire        emit_trigger,     // Trigger wavefront emission
    input wire [15:0] emitter_id,       // Emitter identifier
    output reg [15:0] wavefront_value,   // Computed wavefront value
    output reg        wavefront_valid
);
```

**Key Functions**:

1. **Distance Calculation**:
   - Manhattan distance between emitter and observation point
   - Simplified for Q16.16 fixed-point arithmetic
   - Input: x1, y1, x2, y2 coordinates
   - Output: Distance in Q16.16

2. **Wavefront Computation**:
   - decayed_amplitude = amplitude - (distance * decay_rate)
   - phase_shift = frequency * distance (parity only)
   - oscillation = +1 if phase_shift even, -1 if odd
   - value = decayed_amplitude * oscillation

**Parameters**:
- DEFAULT_AMPLITUDE: 16'h7FFF (1.0)
- DEFAULT_FREQUENCY: 16'h0CCC (0.1)
- WAVE_SPEED: 16'h7FFF (1.0)
- DECAY_RATE: 16'h028F (0.01)
- WAVE_DISTANCE: 16'h000A (10.0 units)

### Simulation Results

**Test Harness**: `wavefront_emitter_tb.cpp`

**Test Cases**:
1. Default wavefront at origin: wavefront_value = 0x7FFF (max amplitude) ✓
2. Wavefront at distance (decay effect): wavefront_value = 0x7FFE ✓
3. High frequency wavefront: wavefront_value = 0x7FFF ✓
4. Low amplitude wavefront: wavefront_value = 0x2000 ✓

**Convergence Testing**: 10 consecutive runs showed zero divergence - all runs produced identical results.

---

## Build and Simulation Instructions

### Verilator Simulation

**Prerequisites**:
- Verilator 5.046
- g++ compiler
- pthread library

**Spectral Encoder**:
```bash
cd /tmp/spectral_sim
verilator -Wall --cc spectral_encoder.v --exe spectral_encoder_tb.cpp
cd obj_dir
make -f Vspectral_encoder.mk
./Vspectral_encoder
```

**Wavefront Emitter**:
```bash
cd /tmp/wavefront_sim
verilator -Wall --cc wavefront_emitter.v --exe wavefront_emitter_tb.cpp
cd obj_dir
make -f Vwavefront_emitter.mk
./Vwavefront_emitter
```

### Ngspice Circuit Simulation

**Prerequisites**:
- ngspice (SPICE circuit simulator)

**Spectral Encoder Circuit**:
```bash
cd /tmp/wavefront_sim
ngspice -b spectral_encoder_simple_spice.cir
```

---

## File Locations

### Verilog Source Files
- `4-Infrastructure/hardware/spectral_encoder.v` - Spectral encoder implementation
- `4-Infrastructure/hardware/wavefront_emitter.v` - Wavefront emitter implementation

### Test Harnesses
- `4-Infrastructure/hardware/spectral_encoder_tb.cpp` - Spectral encoder test harness
- `4-Infrastructure/hardware/wavefront_emitter_tb.cpp` - Wavefront emitter test harness

### SPICE Circuit Files
- `4-Infrastructure/hardware/spectral_encoder_simple_spice.cir` - Analog circuit simulation

### Lean Formalizations
- `0-Core-Formalism/lean/Semantics/Semantics/Spectrum.lean` - Spectral encoding theory
- `0-Core-Formalism/lean/Semantics/Semantics/WavefrontEmitter.lean` - Wavefront emission theory

---

## Design Decisions

### Q16.16 Fixed-Point Arithmetic
- Chosen for hardware compatibility
- Provides sufficient precision for signal processing
- Avoids floating-point hardware requirements
- Consistent with Lean formalization approach

### Verilator Compatibility
- Individual output ports instead of arrays (Verilator limitation)
- Lint directives for unused signals/parameters
- Simplified for loops to avoid Verilator restrictions

### SPICE Circuit Simplification
- Basic RC integrator model for spectral bins
- Pulse inputs for genetic events
- Avoided complex voltage-controlled sources for simulation stability

---

## Performance Characteristics

### Spectral Encoder
- Latency: 1 clock cycle per event
- Throughput: 1 event per clock cycle
- Resource usage: Minimal (combinational logic + 8 registers)
- Deterministic: Zero divergence across 10 runs

### Wavefront Emitter
- Latency: 1 clock cycle per emission
- Throughput: 1 emission per clock cycle
- Resource usage: Minimal (combinational logic + state registers)
- Deterministic: Zero divergence across 10 runs

---

## Future Work

### Additional Signal Theory Modules
- Morphic DSP theory conversion to Verilog
- Hydrogen spectral basis conversion to Verilog
- DSP-aware erasure coding implementation
- Mutual information signal processing

### Enhanced Simulations
- More complex SPICE circuits with active components
- Mixed-signal simulation (digital + analog)
- Power consumption analysis
- Timing analysis for FPGA synthesis

### Integration
- Integration with braid_serial_top module
- Multi-module simulation scenarios
- Hardware-in-the-loop testing

---

## References

- Signal Theory Compendium: `SIGNAL_THEORY_COMPENDIUM.md`
- Lean formalizations: `0-Core-Formalism/lean/Semantics/`
- Verilator documentation: https://verilator.org
- ngspice documentation: https://ngspice.sourceforge.io

---

## Version History

- 2026-05-07: Initial implementation of spectral encoder and wavefront emitter
- 2026-05-07: Verilator simulation and convergence testing
- 2026-05-07: Ngspice circuit simulation
- 2026-05-07: Documentation
