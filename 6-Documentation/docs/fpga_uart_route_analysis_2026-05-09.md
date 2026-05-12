# FPGA UART Route Analysis

**Date:** 2026-05-09
**Board:** Tang Nano 9K / Gowin GW1N(R)-9C
**Status:** USB-UART bridge path blocked; external adapter solution required

## Current Situation

### Problem Summary
The Tang Nano 9K USB-UART bridge is not routing fabric UART to `/dev/ttyUSB0` or `/dev/ttyUSB1`. Both standard and swapped pin configurations have been tested with TX-only beacon bitstreams, and no fabric UART bytes were observed on either device.

This route failure does not erase the custom FPGA work already completed. The Q16.16 accelerator RTL, open-source build script, Lean-linked opcodes, host receipt harness, and TX-only beacon are custom surfaces for this stack. The current blocker is specifically the live serial route from host to fabric.

### Evidence of Blockage

**Beacon Test Results:**
- Standard pin config (TX=17, RX=18): No beacon bytes on `/dev/ttyUSB0` or `/dev/ttyUSB1`
- Swapped pin config (TX=18, RX=17): No beacon bytes on `/dev/ttyUSB0` or `/dev/ttyUSB1`
- Beacon pattern: `A6 42 51 31 36 0A` (0xA6 + beacon version 0x42 + ASCII "Q16\n")

**Control Test Results:**
- Preexisting UART loopback bitstream also produced no `/dev/ttyUSB1` fabric response
- `/dev/ttyUSB0` shows FTDI MPSSE/JTAG command echoes (`faXX` patterns)
- This confirms the blocker is the USB-UART-to-fabric pin path, not Q16 arithmetic synthesis

**Forced JTAG Clear Results:**
- `openFPGALoader --detect` sees the Gowin `GW1N(R)-9C` over the FT2232 JTAG path
- JTAG reset and SRAM reload of the TX-only beacon complete with `CRC check: Success`
- Beacon probe after forced JTAG reset/reload still reads zero bytes on `/dev/ttyUSB0` and `/dev/ttyUSB1`
- Loading the loopback bitstream after the JTAG clear produced `faXX`-style bytes on `/dev/ttyUSB0`, matching FTDI/MPSSE bridge behavior rather than the expected fabric beacon payload
- Reloading the Q16 accelerator to SRAM succeeds, but hardware receipts still return empty/short frames

**JTAG Clear Conclusion:**
The forced JTAG clear confirms that the USB-UART bridge issue is not a stale state or configuration problem that can be resolved by JTAG reset. The `faXX` patterns are definitively FTDI/MPSSE bridge behavior, not fabric UART responses. The BL702 bridge appears to be operating in JTAG/MPSSE mode only, not transparent UART bridge mode for fabric communication.

**Virtual Serial Control:**
- A PTY-backed virtual serial responder was added to exercise the same Q16 host framing and receipt parser without live FPGA fabric
- The virtual serial probe passes shift, weighted, and monotone Q16 operations
- This narrows the remaining failure to the physical/JTAG-bridge-to-fabric route, not the host protocol encoder, parser, or opcode semantics
- Machine receipt: `shared-data/data/stack_solidification/tang9k_rrc_q16_virtual_serial_probe.json`

**Transport Router Control:**
- The UART routes are now represented as a route table rather than loose device paths
- The active non-hardware route is `virtual://q16-pty`
- Onboard FTDI routes remain visible as blocked physical entries, and the external USB-UART route remains the required live-hardware closure path
- Machine receipt: `shared-data/data/stack_solidification/tang9k_uart_transport_routes.json`

## Current Pin Assignments

### Standard Configuration (tangnano9k_uart_loopback.cst)
```
IO_LOC "uart_tx_pin" 17;
IO_LOC "uart_rx_pin" 18;
```

### Swapped Configuration (tangnano9k_uart_swapped.cst)
```
IO_LOC "uart_tx_pin" 18;
IO_LOC "uart_rx_pin" 17;
```

### Sparkle Project Reference
```
// USB-UART via onboard BL702.
IO_LOC "uart_tx" 17;
```

## Root Cause Analysis

### Likely Issue: BL702 Bridge Configuration
The Tang Nano 9K uses an onboard BL702 microcontroller as a USB-UART bridge. The BL702 may be:
1. Configured for JTAG/MPSSE mode only (not UART bridge mode)
2. Not routing the expected fabric pins to the USB UART endpoints
3. Requiring specific configuration commands to enable UART bridging

### Alternative Issue: Pin Multiplexing
The physical pins 17/18 may be multiplexed with other functions:
- Could be configured as GPIO instead of UART
- May require BL702 firmware configuration
- Bridge may not be in transparent UART mode

## Proposed Solution: External USB-UART Adapter

### Rationale
Since the onboard BL702 bridge is not functioning as expected, the most reliable path forward is to bypass it entirely and use an external USB-UART adapter connected directly to the fabric pins.

### Implementation Plan

#### Hardware Required
- External USB-UART adapter (FTDI or CP210x based)
- Connection wires (female-to-female dupont cables)
- Access to Tang Nano 9K GPIO header pins 17 and 18

#### Connection Diagram
```
External USB-UART Adapter    Tang Nano 9K
------------------------    --------------
TX (adapter)  -------->  RX (pin 18)
RX (adapter)  <--------  TX (pin 17)
GND           -------->  GND
```

#### Software Steps
1. Identify external USB-UART device (e.g., `/dev/ttyUSB2` or `/dev/ttyACM0`)
2. Modify probe scripts to use external device path
3. Rebuild beacon bitstream with standard pin assignment (TX=17, RX=18)
4. Load beacon bitstream to FPGA via SRAM
5. Test beacon reception on external UART device
6. If beacon succeeds, proceed to Q16 accelerator testing

#### Modified Probe Commands
```bash
# Test beacon with external adapter
python3 4-Infrastructure/shim/tang9k_uart_beacon_probe.py --port /dev/ttyUSB2

# Test Q16 operations with external adapter
python3 4-Infrastructure/shim/tang9k_rrc_q16_accel.py --op shift --x 0x00038000 --port /dev/ttyUSB2
python3 4-Infrastructure/shim/tang9k_rrc_q16_accel.py --op weighted --energy 0x000a0000 --alpha 0x00008000 --port /dev/ttyUSB2
python3 4-Infrastructure/shim/tang9k_rrc_q16_accel.py --op monotone --a 0x00010000 --b 0x00030000 --port /dev/ttyUSB2
```

## Fallback: BL702 Bridge Investigation

If external adapter is not available, investigate BL702 bridge configuration:

### Investigation Steps
1. Obtain Tang Nano 9K board schematic and BL702 documentation
2. Check if BL702 requires firmware update or configuration
3. Test with Gowin official toolchain to see if they use different pin assignments
4. Examine BL702 USB descriptors to determine current mode
5. Research if BL702 can be reconfigured or if alternative bridge mode exists

### Risk Assessment
- BL702 configuration may be board-specific and not publicly documented
- Firmware updates may brick the bridge if not done correctly
- Time investment may be high with uncertain success probability

## Recommendation

**Primary Path:** Use external USB-UART adapter
- Higher probability of success
- Bypasses undocumented BL702 behavior
- Provides direct fabric access for debugging
- Minimal configuration required

**Secondary Path:** BL702 bridge investigation
- Only pursue if external adapter unavailable
- Requires board documentation research
- May need Gowin vendor support
- Higher risk and time investment

## Next Actions

1. **Immediate:** Acquire or locate external USB-UART adapter
2. **Hardware:** Connect adapter to Tang Nano 9K pins 17 (TX) and 18 (RX)
3. **Software:** Identify adapter device path and modify probe scripts
4. **Test:** Run beacon probe with external adapter
5. **Validate:** If beacon succeeds, proceed to Q16 accelerator testing
6. **Document:** Update FPGA setup documentation with external adapter procedure

## Success Criteria

- Beacon pattern `A6 42 51 31 36 0A` received on external UART device
- Q16 shift operation returns correct hardware receipt
- Q16 weighted term operation returns correct hardware receipt
- Q16 monotone operation returns correct hardware receipt
- All operations match software receipt expectations

## References

- Original FPGA setup: `6-Documentation/docs/fpga_rrc_q16_accel_setup_2026-05-09.md`
- Superseded probe report: `6-Documentation/docs/fpga_direct_probe_report_2026-05-09.md`
- Hardware constraint files: `4-Infrastructure/hardware/tangnano9k_uart_*.cst`
