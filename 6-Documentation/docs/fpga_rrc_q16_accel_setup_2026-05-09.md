# FPGA Rainbow Raccoon Q16 Accelerator Setup

**Date:** 2026-05-09
**Board:** Tang Nano 9K / Gowin GW1N(R)-9C
**Status:** Bitstream builds and loads to SRAM; USB-UART path is not currently receiving fabric UART responses.

## Added Surface

Created a narrow FPGA witness lane for Rainbow Raccoon Compiler fixed-point lowering:

- `4-Infrastructure/hardware/tangnano9k_rrc_q16_accel.v`
- `4-Infrastructure/hardware/build_rrc_q16_accel.sh`
- `4-Infrastructure/shim/tang9k_rrc_q16_accel.py`

This is custom hardware work, not an off-the-shelf Gowin example. The RTL defines a purpose-built Q16.16 arithmetic witness surface for the Rainbow Raccoon pipeline, the build script targets that surface through the open-source Gowin flow, and the host shim emits machine receipts for each deterministic witness operation.

The hardware surface accepts framed UART requests:

```text
A5 02 seq opcode len payload crc8
```

and returns:

```text
A6 02 seq status len payload crc8
```

## Opcodes

| Opcode | Meaning | Lean receipt lane |
| --- | --- | --- |
| `0x20` | `x >>> 16` Q16.16 divide-by-65536 witness | `shiftRightEqDiv` |
| `0x21` | `(E * alpha) >>> 16 <= E` bounded weighted term witness | `weightedTermBounded` |
| `0x22` | monotone arithmetic shift witness | `shiftRightMonotone` |

The FPGA surface is intentionally not a proof authority. It accelerates deterministic arithmetic witnesses only; Lean and the host admission path remain authoritative.

## Custom Work Boundary

Accurate claim:

> This is a custom hardware witness surface for Lean-linked Q16.16 arithmetic lowering, built for the Rainbow Raccoon pipeline. The bitstream builds and SRAM-loads, and the software witness lane passes. Live FPGA receipts remain blocked by the UART/fabric route, not by the Q16 arithmetic design.

This boundary matters: build success, SRAM load, and software witness receipts are real evidence, but hardware acceleration is not promoted until the UART route returns matching hardware receipts.

## Build Evidence

Command:

```bash
cd 4-Infrastructure/hardware
./build_rrc_q16_accel.sh
```

Result:

- Yosys synthesis: pass, 0 check problems
- nextpnr-himbaechel: pass at 27 MHz
- Maximum reported clock frequency after route: `102.13 MHz`
- Device usage: `730/8640 LUT4`, `269/6480 DFF`, `1/5 MULT36X36`
- Bitstream SHA-256: `cdd8ae8f089c0b6dc5b638b112a3f4662497f2cee1b240cd5fcdb939b67166ff`

## Programming Evidence

SRAM load succeeds:

```bash
openFPGALoader -b tangnano9k 4-Infrastructure/hardware/tangnano9k_rrc_q16_accel.fs
```

Result:

```text
Load SRAM: 100.00%
CRC check: Success
```

Flash programming attempt was not accepted as durable:

```text
write Flash: 100.00%
CRC check : FAIL
Read: 0x00000000 checksum: 0x5c15
```

Use SRAM load for now. Do not claim persistent flash install until the flash readback failure is resolved.

## Host Receipts

Software receipt checks pass:

- `4-Infrastructure/shim/tang9k_rrc_q16_accel_shift_software_receipt.json`
- `4-Infrastructure/shim/tang9k_rrc_q16_accel_weighted_software_receipt.json`
- `4-Infrastructure/shim/tang9k_rrc_q16_accel_monotone_software_receipt.json`

USB-UART hardware receipt checks currently fail with no response on `/dev/ttyUSB1`:

- `4-Infrastructure/shim/tang9k_rrc_q16_accel_shift_hw_receipt.json`
- `4-Infrastructure/shim/tang9k_rrc_q16_accel_weighted_hw_receipt.json`
- `4-Infrastructure/shim/tang9k_rrc_q16_accel_monotone_hw_receipt.json`

A control test with the preexisting UART loopback bitstream also produced no `/dev/ttyUSB1` fabric response, while `/dev/ttyUSB0` shows FTDI MPSSE/JTAG command echoes such as `faXX`. Therefore the present blocker is the USB-UART-to-fabric pin path, not Q16 arithmetic synthesis.

A forced JTAG reset and SRAM reload was also tested. The JTAG path detects the Gowin device and reloads bitstreams successfully, but the beacon and Q16 hardware receipts remain silent on the host-visible serial endpoints. This makes the next useful test an external USB-UART adapter on the fabric pins, not another JTAG clear loop.

A PTY-backed virtual serial responder was added as a host-side control. It passes the same shift, weighted, and monotone Q16 operations through the existing serial harness, which confirms the host framing and receipt parser are working independently of the blocked physical UART route.

The UART path is now modeled through a transport route table. The active non-hardware route is `virtual://q16-pty`, while `/dev/ttyUSB0` and `/dev/ttyUSB1` remain blocked physical route entries. This lets the Rainbow Raccoon pipeline continue exercising serial receipts without confusing virtual-route success for live FPGA fabric success.

## UART Beacon Isolation

To remove the Q16 protocol parser from the failure surface, a TX-only fabric beacon was added:

- `4-Infrastructure/hardware/tangnano9k_uart_beacon.v`
- `4-Infrastructure/hardware/build_uart_beacon.sh`

The beacon repeatedly emits:

```text
A6 42 51 31 36 0A
```

which is the byte `0xA6`, beacon version byte `0x42`, followed by ASCII `Q16\n`.

Two beacon builds were tested:

| Constraint set | TX pin | RX pin | Bitstream SHA-256 | Probe receipt | Result |
| --- | ---: | ---: | --- | --- | --- |
| `tangnano9k_uart_loopback.cst` | 17 | 18 | `45feef98a527b4b1643dcbee983e1b36f9505a0170e0bd03abee65ccca30db17` | `4-Infrastructure/shim/tang9k_uart_beacon_probe_receipt.json` | no beacon bytes on `/dev/ttyUSB0` or `/dev/ttyUSB1` |
| `tangnano9k_uart_swapped.cst` | 18 | 17 | `46d68bd12371f203839c289e7bd7667ebdc33dafd0d6d2f33f9cc7caacc7b86d` | `4-Infrastructure/shim/tang9k_uart_beacon_swapped_probe_receipt.json` | no beacon bytes on `/dev/ttyUSB0` or `/dev/ttyUSB1` |

The second beacon uses an internal reset counter rather than relying on the external reset pin. This means the current blocker is no longer attributable to the Q16 parser, the host framing code, an external reset hold, or a simple TX/RX swap. Treat the live-hardware claim as blocked until the USB-UART bridge mode or physical UART route is verified with board documentation, BL702 bridge configuration, or an external USB-UART adapter on the fabric pins.

See the dedicated route analysis for the current hardware conclusion and external-adapter path:

- `6-Documentation/docs/fpga_uart_route_analysis_2026-05-09.md`

## Current Claim Boundary

What is ready:

- Open-source Gowin build pipeline for this accelerator
- SRAM-loaded FPGA bitstream
- Host-side framed Q16 receipt harness
- PTY-backed virtual serial control for host protocol validation
- Lean-linked opcode contract

What is not ready:

- Durable flash programming
- Live USB-UART fabric receipts
- Integration into automatic Rainbow Raccoon Compiler routing

## Next Fix

Resolve the UART physical route:

1. Confirm Tang Nano 9K USB-UART bridge mode and pins for this board revision.
2. If the onboard USB bridge is not routing fabric UART to `/dev/ttyUSB1`, attach an external USB-UART adapter to the actual fabric pins and re-run the beacon first.
3. Re-run the simple loopback or TX-only beacon bitstream before testing the Q16 accelerator.
4. Once the beacon responds, re-run:

```bash
python3 4-Infrastructure/shim/tang9k_uart_beacon_probe.py --port /dev/ttyUSB2
python3 4-Infrastructure/shim/tang9k_rrc_q16_accel.py --op shift --x 0x00038000 --port /dev/ttyUSB2
python3 4-Infrastructure/shim/tang9k_rrc_q16_accel.py --op weighted --energy 0x000a0000 --alpha 0x00008000 --port /dev/ttyUSB2
python3 4-Infrastructure/shim/tang9k_rrc_q16_accel.py --op monotone --a 0x00010000 --b 0x00030000 --port /dev/ttyUSB2
```

Use the actual external adapter path if it enumerates as a different device, for example `/dev/ttyACM0`.
