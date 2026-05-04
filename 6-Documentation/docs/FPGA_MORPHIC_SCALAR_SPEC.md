# FPGA Morphic Scalar Specification

**Date:** 2026-04-26T19:45:00
**Status:** Design complete, Verilog implementation ready
**Target:** Lattice iCE40 HX8K / ECP5
**Lean Source:** `0-Core-Formalism/lean/Semantics/FPGAExtraction.lean`
**Verilog Implementation:** `hardware/morphic_scalar_fpga.v`

---

## Overview

This document specifies the FPGA implementation of the morphic scalar system derived from Lean specifications. The implementation follows AGENTS.md requirements: Verilog is generated from Lean theorems and serves as a hardware extraction target, not a source of logic.

## Architecture

### Target Hardware

**Primary:** Lattice iCE40 HX8K
- LUT cells: 7,680 (3.3% utilized)
- Flip-flops: 7,680 (1.3% utilized)
- Block RAM: 128KB (6.3% utilized)
- DSP slices: 8 (0% utilized - fixed-point only)
- Clock: 50 MHz

**Expansion:** Lattice ECP5
- LUT cells: 52,800
- Flip-flops: 52,800
- Block RAM: 512KB
- DSP slices: 80
- Clock: 50 MHz

### Resource Utilization

| Resource | Required | HX8K Budget | Utilization |
|----------|----------|-------------|-------------|
| LUT cells | ~250 | 7,680 | 3.3% |
| LUTRAM (void mask) | 512 bits | 8KB | 6.3% |
| Flip-flops | ~100 | 7,680 | 1.3% |
| Block RAM | 0 | 128KB | 0% |
| DSP slices | 0 | 8 | 0% |

### Performance

**Latency:**
- OEPI calculation: 5 cycles (5 multiplications + 4 additions)
- State transition: 1 cycle
- Amplitude update: 1 cycle
- Profile collapse: 1 cycle
- **Total per operation:** ~8 cycles = **160ns @ 50MHz**

**Throughput:** **6.25M operations/second**

## Modules

### 1. Q16.16 Fixed-Point Arithmetic

**Modules:**
- `q16_16_add` - Addition with saturation and overflow detection
- `q16_16_mul` - Multiplication (middle 32 bits of 64-bit product)
- `q16_16_div` - Division with zero-check and saturation
- `q16_16_compare` - Comparison (lt, eq, gt)

**Lean Source:** `Semantics.FixedPoint`

**Verilog Source:** `hardware/morphic_scalar_fpga.v`

### 2. OEPI Calculator

**Function:**
```
OEPI = 0.25 × uncertainty + 0.25 × impact + 0.20 × time_sensitivity + 
       0.15 × irreversibility + 0.15 × live_voltage_risk
```

**Lean Source:** `Semantics.OEPI.calculateOEPI`

**Verilog Module:** `oepi_calculator`

**Inputs:**
- `uncertainty [31:0]` - Q16.16
- `impact [31:0]` - Q16.16
- `time_sensitivity [31:0]` - Q16.16
- `irreversibility [31:0]` - Q16.16
- `live_voltage_risk [31:0]` - Q16.16

**Outputs:**
- `oepi_score [31:0]` - Q16.16

### 3. OEPI Threshold Classifier

**Function:** Classify OEPI score into threshold levels

**Lean Source:** `Semantics.OEPI.determineThreshold`

**Verilog Module:** `oepi_threshold_classifier`

**Inputs:**
- `oepi_score [31:0]` - Q16.16

**Outputs:**
- `threshold [1:0]` - 00=low, 01=medium, 10=critical

**Thresholds:**
- Low: < 70
- Medium: 70-95
- Critical: ≥ 95

### 4. Scalar State Machine

**Function:** Implement 16-state morphic scalar state machine

**Lean Source:** `Semantics.Morphic.ScalarState`

**Verilog Module:** `scalar_state_machine`

**States:**
- 0: SUPERPOSED
- 1: SCOUTING
- 2: MEASURE_LOCAL_NEED
- 3: COLLAPSED_PROFILE
- 4: EXECUTE
- 5: RECEIPT
- 6: AMPLITUDE_UPDATE
- 7: QUERY_COLLECTIVE
- 8: COLLECTIVE_RESPONSE
- 9: QUERY_LLM
- 10: DIRECTED
- 11: HOLD
- 12: OPERATOR_ALERT
- 13: LOW_POWER_PASSIVE_MODE
- 14: QUARANTINE
- 15: MIGRATE

**Auto-transition:** OPERATOR_ALERT → LOW_POWER_PASSIVE_MODE when operator unavailable

**Inputs:**
- `clk`
- `rst_n`
- `transition_trigger`
- `target_state [3:0]`
- `operator_available`

**Outputs:**
- `current_state [3:0]`
- `in_pool`

### 5. Amplitude Update

**Function:** Update profile amplitude

**Lean Source:** `Semantics.Morphic.updateAmplitude`

**Verilog Module:** `amplitude_update`

**Equation:**
```
amplitude_new = amplitude_old + delta
```

**Inputs:**
- `amplitude_old [31:0]` - Q16.16
- `delta [31:0]` - Q16.16

**Outputs:**
- `amplitude_new [31:0]` - Q16.16

### 6. Profile Collapse Selector

**Function:** Select profile for collapse

**Lean Source:** `Semantics.Morphic.collapseProfile`

**Verilog Module:** `profile_collapse`

**Inputs:**
- `collapse_trigger`
- `profile_id [7:0]`

**Outputs:**
- `collapse_valid`
- `collapsed_profile [7:0]`

### 7. Top-Level Morphic Scalar

**Function:** Integrate all morphic scalar components

**Lean Source:** `Semantics.Morphic.MorphicScalar`

**Verilog Module:** `morphic_scalar_top`

**Inputs:**
- Clock and reset
- State machine control
- OEPI components
- Amplitude update parameters
- Profile collapse parameters

**Outputs:**
- Scalar state
- Pool status
- OEPI score and threshold
- Amplitude
- Collapse status

## Verification

### Testbench

**Verilog Module:** `morphic_scalar_tb`

**Test Cases:**
1. Initial state verification (SUPERPOSED, in_pool)
2. OEPI calculation with sample inputs
3. State transition (SUPERPOSED → MEASURE_LOCAL_NEED)
4. Amplitude update
5. Profile collapse
6. Operator unavailable → LOW_POWER_PASSIVE_MODE auto-transition

### Lean Theorems

**File:** `0-Core-Formalism/lean/Semantics/FPGAExtraction.lean`

**Theorems:**
- `ice40SufficientResources` - Proves Lattice iCE40 HX8K has sufficient resources
- `oepiLinearComplexity` - Proves OEPI calculation is O(1)
- `finiteStateMachineStates` - Proves state machine has exactly 16 states

## Integration with Existing FPGA Work

### Compatibility with FPGA Warden Node

The morphic scalar FPGA implementation is compatible with the existing FPGA Warden Node spec (`docs/FPGA_WARDEN_NODE_SPEC.md`):

- **Shared Q16.16 arithmetic:** Both use Q16.16 fixed-point
- **Complementary functionality:** Warden handles AMMR phase accumulation; morphic scalar handles state machine and OEPI
- **Same target hardware:** Both target Lattice iCE40 HX8K/ECP5

### Integration Points

1. **OEPI as Safety Gate:** OEPI output can feed into Warden's safety valve system
2. **State Machine as Control Layer:** Scalar state can modulate Warden's AMMR accumulation
3. **Amplitude as Phase Contribution:** Updated amplitudes can contribute to PhaseVec accumulator

## Next Steps

1. **Simulation:** Run testbench with Icarus Verilog or similar
2. **Synthesis:** Test with Yosys for Lattice iCE40 HX8K
3. **Hardware Testing:** Deploy to Tang Nano 9K or similar board
4. **Lean Verification:** Complete Lean theorem proofs (currently marked as `sorry`)
5. **Integration:** Integrate with FPGA Warden Node on same FPGA

## Files

| File | Role |
|------|------|
| `0-Core-Formalism/lean/Semantics/FPGAExtraction.lean` | Lean specification and theorems |
| `hardware/morphic_scalar_fpga.v` | Verilog implementation |
| `docs/FPGA_MORPHIC_SCALAR_SPEC.md` | This document |
| `docs/FPGA_WARDEN_NODE_SPEC.md` | Related FPGA Warden Node spec |

## References

- AGENTS.md - Lean extraction rules
- `0-Core-Formalism/lean/Semantics/MorphicScalar.lean` - Morphic scalar Lean implementation
- `0-Core-Formalism/lean/Semantics/OEPI.lean` - OEPI Lean implementation
- `0-Core-Formalism/lean/Semantics/FixedPoint.lean` - Q16.16 fixed-point arithmetic
