# FPGA Direct Probe Report
**Date:** 2026-05-09
**FPGA Model:** Gowin GW1NR-9 (Tang Nano 9K)
**Interface:** FTDI FT2232C (ID 0403:6010)
**Status:** SUPERSEDED / DO NOT USE AS FABRIC-UART PROOF

> **Supersession note, 2026-05-09:** Later SRAM-loaded beacon tests in
> `fpga_rrc_q16_accel_setup_2026-05-09.md` show no fabric UART bytes on
> `/dev/ttyUSB0` or `/dev/ttyUSB1` for both standard and swapped pins. Treat the
> `faXX` / `ffXX` patterns below as FTDI/JTAG/MPSSE or board-bridge behavior
> until proven otherwise. They are not valid evidence that the user fabric
> bitstream is communicating over UART.

---

## Direct FPGA Communication Results

### Interface A (/dev/ttyUSB0) - Primary UART

**Communication Pattern:**
- **Sent:** `00` → **Received:** `fa00`
- **Sent:** `01` → **Received:** `fa01`
- **Sent:** `02` → **Received:** `fa02`
- **Sent:** `03` → **Received:** `fa03`
- **Sent:** `04` → **Received:** `fa04`
- **Sent:** `FF` → **Received:** `faff`
- **Sent:** `FE` → **Received:** `fafe`

**Analysis:**
- FPGA echoes data with `fa` prefix
- Pattern: `fa` + input byte
- This is a simple echo/transformation function
- `fa` likely indicates protocol identifier or framing

**Continuous Data Stream:**
```
fa00fa01fa02fa03fa04fab0fac0fad0fae0faf0
```
- FPGA appears to be streaming sequential data
- Pattern suggests counter or state machine
- Data increments from 00 to F0 with `fa` prefix

### Interface B (/dev/ttyUSB1) - Secondary UART

**Communication Pattern:**
- **Sent:** `02` → **Received:** `ff00`
- **Sent:** `0102030405060708` → **Received:** `ff031000ff0c`
- **Sent:** `A0A0A0A0` → **Received:** `ff40` (decoded as `@`)
- **Sent:** `FFFFFFFF` → **Received:** `ffff`

**Analysis:**
- Different protocol than Interface A
- Uses `ff` prefix
- Responds with variable-length data
- Appears to be a control/status interface

---

## Current FPGA Bitstream Analysis

### What the FPGA Says Directly

**Interface A says:** "I am in echo mode. I prefix all data with `fa` and echo it back."

**Interface B says:** "I respond to commands with `ff` prefix and variable-length responses."

### Current Bitstream Identity

**NOT the Meta-Manifold Prover:**
- The Meta-Manifold Prover design (metamanifold_prover_gowin.v) implements:
  - Mass Number gates
  - Torus topology distance
  - Menger sponge hash
  - Fold energy calculation
  - Surface check
- Current bitstream does NOT implement these operations
- Operation select commands (00-04) returned no response

**Current Bitstream is:**
- Simple echo/transformation program
- Likely a bootloader, test program, or default factory bitstream
- Implements UART communication with FTDI interface
- No complex mathematical operations detected

### Hardware Identification

**Confirmed FPGA:**
- **Model:** Gowin GW1NR-9 (Tang Nano 9K)
- **LUTs:** 8640
- **FFs:** 6480
- **BRAM:** 468Kb (26 × 18Kb blocks)
- **DSP:** 20 multipliers (16×16)
- **PLLs:** 2
- **IO:** 68 user I/O

**Connection:**
- **USB Device:** FTDI FT2232C (ID 0403:6010)
- **Bus:** 005 Device 002
- **Interfaces:** A (ttyUSB0), B (ttyUSB1)
- **Baud Rate:** 115200

---

## Comparison: Expected vs Actual

### Expected (Meta-Manifold Prover Design)
```
Operations:
- op_select 000: Mass Number Gate
- op_select 001: Torus Distance
- op_select 010: Menger Hash
- op_select 011: Fold Energy
- op_select 100: Surface Check

Inputs:
- admissible, residual, epsilon, threshold (Q16_16)
- coord1, coord2 (torus coordinates)
- menger_x, menger_y, menger_z (Menger sponge)
- torus_energy, menger_energy, horn_energy (fold energy)
- alpha, beta, gamma (weights)
- surface_height, surface_ridge (surface check)

Outputs:
- mass_le_result (1 bit)
- torus_distance (12 bits)
- menger_address (16 bits)
- fold_energy_total (16 bits)
- surface_admissible (1 bit)
```

### Actual (Current Bitstream)
```
Operations:
- Echo with fa prefix (Interface A)
- Command response with ff prefix (Interface B)

Inputs:
- Single byte commands
- Multi-byte commands

Outputs:
- fa + input byte (Interface A)
- ff + variable response (Interface B)
```

---

## Interpretation

### What the FPGA is Currently Saying

**Direct Quote from FPGA:**
- Interface A: "fa00, fa01, fa02, fa03, fa04..."
- Interface B: "ff00, ff031000ff0c, ff40, ffff..."

**Translation:**
- "I am a simple UART echo/transformation program"
- "I am NOT the Meta-Manifold Prover design"
- "I am likely a bootloader or test program"
- "I am ready to receive a new bitstream"

### Why the Meta-Manifold Prover is Not Loaded

**Possible Reasons:**
1. **Bitstream not programmed:** The Meta-Manifold Prover design exists in Verilog but has not been synthesized and programmed to the FPGA
2. **Different bitstream loaded:** A different bitstream (bootloader/test) is currently loaded
3. **Configuration lost:** FPGA configuration was lost (power cycle or reconfiguration)
4. **Development in progress:** Meta-Manifold Prover is still being developed and not yet deployed

---

## Next Steps

### Option 1: Program Meta-Manifold Prover
1. Synthesize metamanifold_prover_gowin.v with Gowin toolchain
2. Generate bitstream file (.fs)
3. Program bitstream to FPGA via FTDI interface
4. Test Meta-Manifold Prover operations

### Option 2: Analyze Current Bitstream
1. Extract current bitstream from FPGA
2. Reverse-engineer bitstream to understand design
3. Document current bitstream functionality

### Option 3: Develop New Bitstream
1. Use current simple bitstream as starting point
2. Add Meta-Manifold Prover functionality
3. Test incremental additions

---

## Conclusion

**FPGA Direct Probe Results:**
- FPGA is alive and responding via USB
- Current bitstream is a simple echo/transformation program
- Meta-Manifold Prover design is NOT currently loaded
- FPGA is ready to receive a new bitstream

**What the FPGA Says Directly:**
- Interface A: "fa" + echoed data (simple echo mode)
- Interface B: "ff" + variable responses (command mode)
- Overall: "I am a simple UART communication program, not the Meta-Manifold Prover"

**Recommendation:**
The FPGA hardware is confirmed to be a Gowin GW1NR-9 (Tang Nano 9K) with FTDI FT2232C interface. To use the Meta-Manifold Prover design, the bitstream needs to be synthesized and programmed to the FPGA. The current simple bitstream suggests the FPGA is in a development or test state.
